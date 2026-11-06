import csv
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import praw

from reddit_lead_scraper import (
    RedditClientError,
    collect_leads,
    create_reddit_client,
    export_leads,
)

NOW = datetime(2026, 11, 4, 12, tzinfo=timezone.utc)


def submission(post_id, title, *, body="", days_ago=1, score=1, permalink=None):
    created = (NOW - timedelta(days=days_ago)).timestamp()
    return SimpleNamespace(
        id=post_id,
        title=title,
        selftext=body,
        created_utc=created,
        score=score,
        permalink=permalink or f"/r/testing/comments/{post_id}/sample/",
    )


class FakeSubreddit:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(self, query, **kwargs):
        self.calls.append((query, kwargs))
        return iter(self.results.get(query, []))


class FakeReddit:
    def __init__(self, results):
        self.subreddits = {"testing": FakeSubreddit(results)}
        self.requested = []

    def subreddit(self, name):
        self.requested.append(name)
        return self.subreddits.setdefault(name, FakeSubreddit({}))


class CollectLeadsTests(unittest.TestCase):
    def test_search_is_configurable_and_deduplicates_post_ids(self):
        shared = submission("a1", "Need SEO and marketing help", score=5)
        reddit = FakeReddit({"seo": [shared], "marketing": [shared]})

        leads = collect_leads(
            reddit,
            ["testing", "testing"],
            ["seo", "marketing"],
            max_results=4,
            lookback_days=7,
            now=NOW,
        )

        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0].post_id, "a1")
        self.assertEqual(leads[0].matched_keywords, ("seo", "marketing"))
        self.assertEqual(leads[0].relevance_score, 100)
        calls = reddit.subreddits["testing"].calls
        self.assertEqual([call[0] for call in calls], ["seo", "marketing"])
        self.assertTrue(all(call[1]["sort"] == "new" for call in calls))
        self.assertTrue(all(call[1]["time_filter"] == "week" for call in calls))
        self.assertTrue(all(call[1]["limit"] == 4 for call in calls))

    def test_date_filter_and_minimum_relevance_are_applied(self):
        reddit = FakeReddit({"seo": [
            submission("recent-one", "need seo", days_ago=1),
            submission("recent-two", "need seo and marketing help", days_ago=2),
            submission("old", "need seo and marketing help", days_ago=9),
        ]})

        leads = collect_leads(
            reddit, ["testing"], ["seo", "marketing help"],
            lookback_days=7, min_matches=2, now=NOW,
        )
        self.assertEqual([lead.post_id for lead in leads], ["recent-two"])

    def test_max_results_is_a_global_cap(self):
        reddit = FakeReddit({"seo": [submission("a", "seo")], "marketing": [submission("b", "marketing")]})
        leads = collect_leads(reddit, ["testing"], ["seo", "marketing"], max_results=1, now=NOW)
        self.assertEqual(len(leads), 1)

    def test_invalid_configuration_is_rejected(self):
        reddit = FakeReddit({})
        with self.assertRaises(ValueError):
            collect_leads(reddit, [], ["seo"])
        with self.assertRaises(ValueError):
            collect_leads(reddit, ["testing"], ["seo"], max_results=0)
        with self.assertRaises(ValueError):
            collect_leads(reddit, ["testing"], ["seo"], min_matches=2)

    def test_api_errors_are_reported_with_community_context(self):
        class BrokenSubreddit:
            def search(self, *_args, **_kwargs):
                raise RuntimeError("network unavailable")
        class BrokenReddit:
            def subreddit(self, _name):
                return BrokenSubreddit()

        with self.assertRaisesRegex(RedditClientError, "r/testing"):
            collect_leads(BrokenReddit(), ["testing"], ["seo"], now=NOW)


class ApprovalGateTests(unittest.TestCase):
    def test_api_is_blocked_without_explicit_approval_before_client_creation(self):
        with patch.object(praw, "Reddit") as reddit_constructor:
            with self.assertRaisesRegex(RedditClientError, "REDDIT_API_APPROVED"):
                create_reddit_client({})
        reddit_constructor.assert_not_called()

    def test_commercial_gate_is_required(self):
        env = {"REDDIT_API_APPROVED": "true"}
        with patch.object(praw, "Reddit") as reddit_constructor:
            with self.assertRaisesRegex(RedditClientError, "REDDIT_COMMERCIAL_APPROVED"):
                create_reddit_client(env)
        reddit_constructor.assert_not_called()

    def test_credentials_are_required(self):
        env = {"REDDIT_API_APPROVED": "true", "REDDIT_COMMERCIAL_APPROVED": "true"}
        with self.assertRaisesRegex(RedditClientError, "REDDIT_CLIENT_ID"):
            create_reddit_client(env)

    def test_approved_client_is_configured_read_only(self):
        env = {
            "REDDIT_API_APPROVED": "true",
            "REDDIT_COMMERCIAL_APPROVED": "true",
            "REDDIT_CLIENT_ID": "test-id",
            "REDDIT_CLIENT_SECRET": "test-secret",
            "REDDIT_USER_AGENT": "script:test:1.0",
        }
        with patch.object(praw, "Reddit", return_value=object()) as reddit_constructor:
            create_reddit_client(env)
        self.assertTrue(reddit_constructor.call_args.kwargs["read_only"])
        self.assertEqual(reddit_constructor.call_args.kwargs["ratelimit_seconds"], 300)


class ExportTests(unittest.TestCase):
    def test_csv_escapes_formula_injection_and_omits_author_data(self):
        lead = collect_leads(
            FakeReddit({"seo": [submission("x1", "=HYPERLINK(\"https://bad\") Need SEO")]}),
            ["testing"], ["seo"], now=NOW,
        )[0]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "nested" / "leads.csv"
            self.assertEqual(export_leads([lead], output, "csv"), 1)
            with output.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
        self.assertTrue(rows[0]["title"].startswith("'=HYPERLINK"))
        self.assertNotIn("author", rows[0])

    def test_json_export_has_only_documented_fields(self):
        lead = collect_leads(
            FakeReddit({"seo": [submission("x2", "Need SEO help")]}),
            ["testing"], ["seo"], now=NOW,
        )[0]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "leads.json"
            export_leads([lead], output, "json")
            row = json.loads(output.read_text(encoding="utf-8"))[0]
        self.assertEqual(set(row), {
            "post_id", "community", "title", "permalink", "created_utc",
            "score", "matched_keywords", "relevance_score",
        })

    def test_unsupported_format_is_rejected(self):
        with self.assertRaises(ValueError):
            export_leads([], Path("unused.xlsx"), "xlsx")


if __name__ == "__main__":
    unittest.main()
