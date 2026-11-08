"""BLOG-017 F5 rollback helper: only moved posts (notion_id), only Source/skipRendering, dry-run by default."""
import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

from src.ssot.notion_io import NotionIO
from tests.test_ssot_engine import FakeClient

SPEC = importlib.util.spec_from_file_location(
    "release_notion_pages", Path(__file__).resolve().parent.parent / "scripts" / "release_notion_pages.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        posts = Path(self.tmp.name) / "content" / "posts"
        self.client = FakeClient()
        self.client.pages["moved-1"] = {"id": "moved-1", "properties": {}}
        self.client._store_props(self.client.pages["moved-1"],
                                 {"Source": {"select": {"name": "hugo"}}, "skipRendering": {"checkbox": True}})
        self.client.pages["moved-2"] = {"id": "moved-2", "properties": {}}  # moved but never synced: Source empty
        self.client._store_props(self.client.pages["moved-2"], {"skipRendering": {"checkbox": False}})
        for slug, front in (("moved", "notion_id: moved-1\n"), ("moved-unsynced", "notion_id: moved-2\n"), ("repo-first", "")):
            (posts / slug).mkdir(parents=True)
            (posts / slug / "index.md").write_text(f"---\ntitle: t\n{front}---\n\nbody\n", encoding="utf-8")

    def run_main(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = release.main(["--repo", self.tmp.name, *argv], io=NotionIO(self.client))
        return code, out.getvalue()

    def test_dry_run_writes_nothing(self):
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("would set ['Source', 'skipRendering'] on moved-1 (moved)", out)
        self.assertEqual([c for c in self.client.calls if c[0] == "PATCH"], [])

    def test_apply_touches_only_moved_pages_and_two_columns(self):
        self.run_main("--apply")
        page = self.client.pages["moved-1"]
        self.assertEqual(page["properties"]["Source"]["select"], {"name": "notion"})
        self.assertFalse(page["properties"]["skipRendering"]["checkbox"])
        self.assertEqual([c for c in self.client.calls if c[0] == "PATCH"], [("PATCH", "pages/moved-1")])
        self.assertIn("0 pages", self.run_main("--apply")[1])  # second run: nothing left


if __name__ == "__main__":
    unittest.main()
