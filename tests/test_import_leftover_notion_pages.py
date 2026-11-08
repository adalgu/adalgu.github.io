"""BLOG-017 F1: only listed Notion pages are imported; a moved post (repo bundle) wins; failures fail."""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path

from tests.test_hugo_source_skip import CONFIG, FakeNotion, page  # noqa: F401

SPEC = importlib.util.spec_from_file_location(
    "import_leftover", Path(__file__).resolve().parent.parent / "scripts" / "import_leftover_notion_pages.py")
leftover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(leftover)


class Notion(FakeNotion):
    def __init__(self, pages):
        super().__init__()
        self.retrieved = []
        outer = self

        class Pages:
            def retrieve(self, page_id):
                outer.retrieved.append(page_id)
                if page_id not in pages:
                    raise RuntimeError("404")
                return pages[page_id]
        self.pages = Pages()


class LeftoverTests(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(os.chdir, self.cwd)
        os.makedirs("content/posts")

    def run_main(self, ids, notion):
        Path("list.txt").write_text("# comment\n\n" + "\n".join(ids) + "\n")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return leftover.main(["--list", "list.txt"], notion=notion)

    def flat(self):
        return sorted(p.name for p in Path("content/posts").glob("*.md"))

    def test_only_listed_pages_are_imported(self):
        notion = Notion({"p-left": page("p-left", "남은 글", slug="left-post"), "p-other": page("p-other", "딴 글", slug="x")})
        self.assertEqual(self.run_main(["p-left"], notion), 0)
        self.assertEqual(notion.retrieved, ["p-left"])
        self.assertEqual(len(self.flat()), 1)
        self.assertIn("slug: left-post", next(Path("content/posts").glob("*.md")).read_text())

    def test_moved_post_bundle_wins(self):
        os.makedirs("content/posts/left-post")
        Path("content/posts/left-post/index.md").write_text("---\ntitle: t\nslug: left-post\n---\n\nrepo\n")
        notion = Notion({"p-left": page("p-left", "남은 글", slug="left-post")})
        self.assertEqual(self.run_main(["p-left"], notion), 0)
        self.assertEqual(self.flat(), [])

    def test_unreadable_page_fails_the_build(self):
        self.assertEqual(self.run_main(["p-gone"], Notion({})), 1)


if __name__ == "__main__":
    unittest.main()
