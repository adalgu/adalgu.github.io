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



# --- 실제 save_page + 가짜 notion: 예외 = 실패(None → errors → exit 1), skipRendering = 건너뜀(errors 0) ---
import os
import tempfile

from src.render import batch_process_pages, save_page
from test_hugo_source_skip import CONFIG, FakeNotion, page


class RaisingNotion:
    def __init__(self):
        self.blocks = type("Blocks", (), {})()
        self.blocks.children = type("C", (), {"list": staticmethod(lambda **kw: (_ for _ in ()).throw(RuntimeError("boom")))})()


class RealSavePageTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(os.chdir, self.cwd)

    def skipped_page(self):
        p = page("p-skip", "건너뜀")
        p["properties"]["skipRendering"]["checkbox"] = True
        return p

    def test_save_page_exception_returns_none_skip_returns_empty(self):
        self.assertIsNone(save_page(page("p1", "글"), RaisingNotion(), "posts", CONFIG))
        self.assertEqual(save_page(self.skipped_page(), FakeNotion(), "posts", CONFIG), "")
        self.assertIn("노션 본문", save_page(page("p2", "글"), FakeNotion(), "posts", CONFIG))

    def test_incremental_exception_is_error_skip_is_not(self):
        bad, _ = _run_real([page("p1", "글")], RaisingNotion())
        self.assertEqual([e["pageId"] for e in bad["errors"]], ["p1"])
        self.assertEqual(bad["success"], [])
        ok, _ = _run_real([self.skipped_page()], FakeNotion())
        self.assertEqual(ok["errors"], [])

    def test_full_sync_exception_is_error_skip_is_not(self):
        bad = batch_process_pages([page("p1", "글")], RaisingNotion(), {"target_folder": "posts"}, CONFIG)
        self.assertEqual([e["pageId"] for e in bad["errors"]], ["p1"])
        ok = batch_process_pages([self.skipped_page()], FakeNotion(), {"target_folder": "posts"}, CONFIG)
        self.assertEqual(ok["errors"], [])
        self.assertEqual([s["pageId"] for s in ok["skipped"]], ["p-skip"])


def _run_real(pages, notion):
    meta = FakeMetadata()
    return notion_hugo.batch_process_pages_with_metadata(pages, notion, MOUNT, meta, CONFIG), meta


if __name__ == "__main__":
    unittest.main()
