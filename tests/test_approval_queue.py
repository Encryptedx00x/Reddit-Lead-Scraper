import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import openclaw_wrapper


class ApprovalQueueTests(unittest.TestCase):
    def test_negative_approval_index_does_not_approve_last_item(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pending = root / "approval_queue.json"
            approved = root / "approved_posts.json"
            pending.write_text(json.dumps([{"lead": {"subreddit": "test"}, "draft": "synthetic"}]))
            with patch.object(openclaw_wrapper, "APPROVAL_QUEUE", pending), patch.object(
                openclaw_wrapper, "APPROVED_QUEUE", approved
            ):
                result = openclaw_wrapper.approve_item(-1)
            self.assertIn("Índice inválido", result)
            self.assertEqual(len(json.loads(pending.read_text())), 1)
            self.assertFalse(approved.exists())

    def test_negative_rejection_index_does_not_remove_last_item(self):
        with tempfile.TemporaryDirectory() as directory:
            pending = Path(directory) / "approval_queue.json"
            pending.write_text(json.dumps([{"lead": {"subreddit": "test"}, "draft": "synthetic"}]))
            with patch.object(openclaw_wrapper, "APPROVAL_QUEUE", pending):
                result = openclaw_wrapper.reject_item(-1)
            self.assertIn("Índice inválido", result)
            self.assertEqual(len(json.loads(pending.read_text())), 1)


if __name__ == "__main__":
    unittest.main()
