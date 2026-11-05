import csv
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from reddit_lead_scraper import Lead, RedditClientError, collect_leads, export_leads, create_reddit_client

NOW = datetime(2026, 11, 5, tzinfo=timezone.utc)


class FinalAuditTests(unittest.TestCase):
    def test_csv_escapes_joined_keyword_cell_too(self):
        lead = Lead('synthetic', 'test', 'Safe title', '/synthetic', 1, 0, ('=1+1',), 100)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.csv'
            export_leads([lead], path, 'csv')
            with path.open(encoding='utf-8-sig', newline='') as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row['matched_keywords'], "'=1+1")

    def test_malformed_and_future_timestamps_do_not_abort_or_enter_results(self):
        def post(name, stamp):
            return SimpleNamespace(id=name, title='seo', selftext='', created_utc=stamp, score=0, permalink='/synthetic')
        rows = [post('nan', float('nan')), post('inf', float('inf')), post('future', NOW.timestamp()+86400), post('valid', NOW.timestamp()-100)]
        client = SimpleNamespace(subreddit=lambda name: SimpleNamespace(search=lambda *args, **kwargs: iter(rows)))
        result = collect_leads(client, ['test'], ['seo'], now=NOW)
        self.assertEqual([r.post_id for r in result], ['valid'])

    def test_client_setup_errors_are_wrapped_without_raw_secret_text(self):
        class Broken:
            def subreddit(self, name):
                raise RuntimeError('synthetic-client-secret')
        with self.assertRaises(RedditClientError) as raised:
            collect_leads(Broken(), ['test'], ['seo'], now=NOW)
        self.assertNotIn('synthetic-client-secret', str(raised.exception))

    def test_generator_errors_are_sanitized(self):
        def broken():
            raise RuntimeError('synthetic-client-secret')
            yield
        client = SimpleNamespace(subreddit=lambda name: SimpleNamespace(search=lambda *args, **kwargs: broken()))
        with self.assertRaises(RedditClientError) as raised:
            collect_leads(client, ['test'], ['seo'], now=NOW)
        self.assertNotIn('synthetic-client-secret', str(raised.exception))

    def test_late_pagination_failure_is_not_returned_as_successful_partial_collection(self):
        def pages():
            yield SimpleNamespace(id='synthetic', title='seo', selftext='', created_utc=NOW.timestamp()-1, score=0, permalink='/synthetic')
            raise RuntimeError('synthetic page failure')
        client = SimpleNamespace(subreddit=lambda name: SimpleNamespace(search=lambda *args, **kwargs: pages()))
        with self.assertRaises(RedditClientError):
            collect_leads(client, ['test'], ['seo'], now=NOW)

    def test_query_budget_is_checked_before_client_access(self):
        client = SimpleNamespace(subreddit=lambda name: self.fail('client accessed before validation'))
        with self.assertRaises(ValueError):
            collect_leads(client, [f'community{n}' for n in range(101)], ['seo'], now=NOW)

    def test_real_praw_constructor_is_read_only_without_network(self):
        with patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden')) as network:
            with create_reddit_client({'REDDIT_API_APPROVED':'true', 'REDDIT_COMMERCIAL_APPROVED':'true', 'REDDIT_CLIENT_ID':'synthetic-id', 'REDDIT_CLIENT_SECRET':'synthetic-secret', 'REDDIT_USER_AGENT':'script:synthetic-audit:1.0'}) as client:
                self.assertTrue(client.read_only)
            network.assert_not_called()
