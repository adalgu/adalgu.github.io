"""TASK-455: incremental path must not report success when save_page returns None (offline, fake pages/metadata)."""
import unittest
from unittest import mock

from src import notion_hugo

MOUNT = {"target_folder": "posts"}


class FakeMetadata:
    def __init__(self):
        self.calls = []

    def update_page_status(self, page_id, **kwargs):
        self.calls.append((page_id, kwargs))

    def compute_content_hash(self, content):
        return f"h:{content}"


def run(contents):
    pages = [{"id": f"p{i}", "last_edited_time": "2026-11-05T00:00:00Z"} for i in range(len(contents))]
    meta = FakeMetadata()
    with mock.patch.object(notion_hugo, "ensure_directory"), \
         mock.patch.object(notion_hugo, "get_page_title", return_value="t"), \
         mock.patch.object(notion_hugo, "save_page", side_effect=contents):
        result = notion_hugo.batch_process_pages_with_metadata(pages, mock.Mock(), MOUNT, meta, {})
    return result, meta


class SavePageNoneTest(unittest.TestCase):
    def test_none_is_an_error_not_a_success(self):
        result, meta = run([None])
        self.assertEqual([e["pageId"] for e in result["errors"]], ["p0"])
        self.assertEqual(result["success"], [])
        self.assertEqual(meta.calls[0][1]["status"], "error")

    def test_none_makes_run_fail_exit_rule(self):
        # same predicate index.py / notion_hugo.py use for sys.exit(1)
        result, _ = run(["body", None])
        self.assertTrue(any(len(r["errors"]) > 0 for r in [result]))

    def test_good_page_still_success_and_counts_add_up(self):
        result, meta = run(["body", None, "more"])
        self.assertEqual([s["pageId"] for s in result["success"]], ["p0", "p2"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["totalProcessed"], len(result["success"]) + len(result["errors"]))
        self.assertEqual([c[1]["status"] for c in meta.calls], ["success", "error", "success"])

    def test_empty_string_stays_as_before(self):
        # '' = skipRendering/handled-inside; not part of TASK-455 (reported only)
        result, _ = run([""])
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
