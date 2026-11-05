# Recovery checkpoint 01 — Reddit Lead Scraper

- Checkout cloned at `C:\Users\Encryptedx\Desktop\Reddit-Lead-Scraper`; branch `codex/recovery`; initial commit `0d2e052`.
- Replaced import-time PRAW initialization and hard-coded one-week scraping with a configurable read-only search function and CLI: communities, keywords, max results, lookback, minimum matched terms, JSON/CSV output.
- Results are deduplicated by post ID, time-filtered locally, scored with a transparent keyword-count heuristic, and omit usernames and full post bodies. CSV values are escaped against spreadsheet formula injection. No posting, comments, votes, or DMs are implemented.
- PRAW is gated behind `REDDIT_API_APPROVED=true` and `REDDIT_COMMERCIAL_APPROVED=true`; those local switches do not grant permission. Current Reddit policy requires explicit API approval, and commercial use requires a separate written agreement. No credentials or evidence of either approval were found, so no live API request was made.
- Added `.env.example`, ignored local credentials/outputs, direct pins and a full lockfile, an accurate README, tests for collection, deduplication, date/relevance limits, error reporting, privacy-safe output, formula escaping, approval gates, and legacy queue index bounds.
- `openclaw_wrapper.py` remains a legacy prototype; it references a fixed Linux path and absent `outreach_engine.py`. Its approval/rejection functions now reject negative indices.

Final validation: `python -m unittest discover -s tests -v` — 14 passed; `pip check` — clean; lock dry-run resolved; isolated `pip-audit -r requirements-lock.txt` — no known vulnerabilities; CLI `--help`, import without API side effects, and no-approval gate verified. All test/API behavior is local or mocked. Python 3.13.14 used.

Status: **FUNCIONAL COM RESSALVAS** — implementation and mock-based checks pass; live operation remains pending Reddit API approval, commercial agreement, and credentials.

References reviewed 2026-11-04:
- Reddit [Data API Terms](https://redditinc.com/policies/data-api-terms)
- Reddit [Developer Terms](https://redditinc.com/policies/developer-terms)
- Reddit [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy)
- PRAW [`Subreddit.search`](https://praw.readthedocs.io/en/stable/code_overview/models/subreddit.html)
