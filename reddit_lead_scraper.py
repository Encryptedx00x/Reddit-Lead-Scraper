"""Read-only Reddit search for approved API use; never posts or sends messages."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

from dotenv import load_dotenv

DEFAULT_COMMUNITIES = ("SEO", "marketing", "Entrepreneur", "smallbusiness", "startups")
DEFAULT_KEYWORDS = ("need seo", "marketing help", "looking for recommendations")
MAX_PER_QUERY = 1000


class RedditClientError(RuntimeError):
    """Configuration, approval, or API failure safe to show to the operator."""


class SearchClient(Protocol):
    def subreddit(self, name: str) -> Any: ...


@dataclass(frozen=True)
class Lead:
    post_id: str
    community: str
    title: str
    permalink: str
    created_utc: int
    score: int
    matched_keywords: tuple[str, ...]
    relevance_score: int

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["matched_keywords"] = list(self.matched_keywords)
        return result


def _clean_items(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        item = value.strip()
        key = item.casefold()
        if item and key not in seen:
            seen.add(key)
            cleaned.append(item)
    return tuple(cleaned)


def _matches(text: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    folded = text.casefold()
    return tuple(keyword for keyword in keywords if keyword.casefold() in folded)


def _time_filter(lookback_days: int) -> str:
    if lookback_days <= 1:
        return "day"
    if lookback_days <= 7:
        return "week"
    if lookback_days <= 30:
        return "month"
    if lookback_days <= 365:
        return "year"
    return "all"


def collect_leads(
    reddit: SearchClient,
    communities: Iterable[str],
    keywords: Iterable[str],
    *,
    max_results: int = 100,
    lookback_days: int = 7,
    min_matches: int = 1,
    now: datetime | None = None,
) -> list[Lead]:
    """Collect matching public posts via a supplied client (easy to mock in tests)."""
    selected_communities = _clean_items(communities)
    selected_keywords = _clean_items(keywords)
    if not selected_communities:
        raise ValueError("Informe ao menos uma comunidade.")
    if not selected_keywords:
        raise ValueError("Informe ao menos uma palavra-chave.")
    if not 1 <= max_results <= 1000:
        raise ValueError("max_results deve estar entre 1 e 1000.")
    if not 1 <= lookback_days <= 3650:
        raise ValueError("lookback_days deve estar entre 1 e 3650.")
    if len(selected_communities) * len(selected_keywords) > 100:
        raise ValueError("A combinação informada excede 100 consultas; reduza comunidades ou termos.")
    if not 1 <= min_matches <= len(selected_keywords):
        raise ValueError("min_matches deve estar entre 1 e o total de palavras-chave.")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now deve incluir fuso horário.")
    cutoff = (current.astimezone(timezone.utc) - timedelta(days=lookback_days)).timestamp()
    time_filter = _time_filter(lookback_days)
    posts: dict[str, Lead] = {}
    query_limit = min(max_results, MAX_PER_QUERY)

    for community in selected_communities:
        subreddit = reddit.subreddit(community)
        for keyword in selected_keywords:
            try:
                results = subreddit.search(
                    keyword,
                    sort="new",
                    time_filter=time_filter,
                    limit=query_limit,
                )
                for submission in results:
                    post_id = str(getattr(submission, "id", "")).strip()
                    title = str(getattr(submission, "title", "") or "").strip()
                    body = str(getattr(submission, "selftext", "") or "")
                    try:
                        created = float(submission.created_utc)
                    except (AttributeError, TypeError, ValueError):
                        continue
                    if not post_id or not title or created < cutoff:
                        continue
                    matches = _matches(f"{title} {body}", selected_keywords)
                    if len(matches) < min_matches or post_id in posts:
                        continue
                    score = getattr(submission, "score", 0)
                    try:
                        score = int(score)
                    except (TypeError, ValueError):
                        score = 0
                    permalink = str(getattr(submission, "permalink", "") or "")
                    if permalink.startswith("/"):
                        permalink = f"https://www.reddit.com{permalink}"
                    relevance = round(100 * len(matches) / len(selected_keywords))
                    posts[post_id] = Lead(
                        post_id=post_id,
                        community=community,
                        title=title,
                        permalink=permalink,
                        created_utc=int(created),
                        score=score,
                        matched_keywords=matches,
                        relevance_score=relevance,
                    )
            except Exception as exc:
                raise RedditClientError(
                    f"Falha na busca em r/{community} para {keyword!r}: {exc}"
                ) from exc
            if len(posts) >= max_results:
                break
        if len(posts) >= max_results:
            break

    ordered = sorted(
        posts.values(),
        key=lambda lead: (-lead.relevance_score, -lead.score, -lead.created_utc, lead.post_id),
    )
    return ordered[:max_results]


def create_reddit_client(environ: Mapping[str, str] | None = None) -> SearchClient:
    """Create a read-only PRAW client only after explicit approval gates pass."""
    env = os.environ if environ is None else environ
    if env.get("REDDIT_API_APPROVED", "").strip().casefold() != "true":
        raise RedditClientError("Configure REDDIT_API_APPROVED=true somente após aprovação expressa do Reddit.")
    if env.get("REDDIT_COMMERCIAL_APPROVED", "").strip().casefold() != "true":
        raise RedditClientError("Uso comercial requer acordo escrito separado; configure REDDIT_COMMERCIAL_APPROVED=true após aprovação.")
    client_id = env.get("REDDIT_CLIENT_ID", "").strip()
    client_secret = env.get("REDDIT_CLIENT_SECRET", "").strip()
    user_agent = env.get("REDDIT_USER_AGENT", "").strip()
    if not all((client_id, client_secret, user_agent)):
        raise RedditClientError("Defina REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET e REDDIT_USER_AGENT no ambiente.")

    try:
        import praw
    except ImportError as exc:
        raise RedditClientError("PRAW não está instalado. Execute: python -m pip install -r requirements-lock.txt") from exc
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        ratelimit_seconds=300,
        read_only=True,
    )


def _spreadsheet_safe(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if re.match(r"^[\s\u0000-\u001f]*[=+@-]", value):
        return "'" + value
    return value


def export_leads(leads: Iterable[Lead], output: Path, format_name: str) -> int:
    rows = [lead.as_dict() for lead in leads]
    output.parent.mkdir(parents=True, exist_ok=True)
    if format_name == "json":
        output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif format_name == "csv":
        fields = list(Lead.__dataclass_fields__)
        with output.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    key: ", ".join(value) if key == "matched_keywords" else _spreadsheet_safe(value)
                    for key, value in row.items()
                })
    else:
        raise ValueError("Formato de saída deve ser json ou csv.")
    return len(rows)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pesquisa somente leitura em comunidades do Reddit aprovadas.")
    parser.add_argument("--communities", default=",".join(DEFAULT_COMMUNITIES), help="Lista separada por vírgulas.")
    parser.add_argument("--keywords", default=",".join(DEFAULT_KEYWORDS), help="Lista separada por vírgulas.")
    parser.add_argument("--max-results", type=int, default=100, help="Limite global de resultados (1–1000).")
    parser.add_argument("--lookback-days", type=int, default=7, help="Janela de busca (1–3650 dias).")
    parser.add_argument("--min-matches", type=int, default=1, help="Mínimo de termos encontrados no título/corpo.")
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = _parser().parse_args(argv)
    extension = args.format
    output = args.output or Path(f"reddit_leads.{extension}")
    try:
        client = create_reddit_client()
        leads = collect_leads(
            client,
            args.communities.split(","),
            args.keywords.split(","),
            max_results=args.max_results,
            lookback_days=args.lookback_days,
            min_matches=args.min_matches,
        )
        total = export_leads(leads, output, args.format)
    except (RedditClientError, ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    print(f"{total} resultados exportados para {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
