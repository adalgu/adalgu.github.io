"""BLOG-018 step 1 (slot r7-P05): published posts without a cover, newest first; drafts and covered posts left out."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("list_missing_covers", ROOT / "scripts" / "list_missing_covers.py")
lister = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lister)


def post(root, slug, front):
    folder = Path(root) / slug
    folder.mkdir(parents=True)
    (folder / "index.md").write_text(f"---\n{front}---\n\n본문\n", encoding="utf-8")


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = lister.main(list(argv))
    return code, out.getvalue()


class ListMissingCovers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        post(root, "old-post", "title: 옛 글\ndate: '2024-01-02'\ndraft: false\n")
        post(root, "new-post", "title: 새 글\ndate: 2026-11-01T09:00:00+09:00\nnotion_id: abc\n")
        post(root, "covered", "title: 커버 있음\ndate: '2026-11-05'\ncover:\n  image: cover.jpg\n")
        post(root, "draft-post", "title: 초안\ndate: '2026-11-08'\ndraft: true\n")
        post(root, "empty-cover", "title: 빈 커버\ndate: '2025-05-05'\ncover:\n  image: ''\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_newest_first_without_cover_or_drafts(self):
        rows = lister.missing(self.tmp.name)
        self.assertEqual([r["slug"] for r in rows], ["new-post", "empty-cover", "old-post"])
        self.assertEqual({r["kind"] for r in rows}, {"Hugo"})
        self.assertEqual([r["notion_id"] for r in rows], [True, False, False])

    def test_limit_and_table(self):
        code, out = run("--posts", self.tmp.name, "--limit", "2")
        self.assertEqual(code, 0)
        lines = [l for l in out.splitlines() if l.startswith("| ") and l[2].isdigit()]
        self.assertEqual(lines, ["| 1 | 2026-11-01 | new-post | Hugo | yes |", "| 2 | 2025-05-05 | empty-cover | Hugo | no |"])
        self.assertIn("2 of 3", out)

    def test_json_and_no_writes(self):
        before = sorted((p, p.stat().st_mtime_ns) for p in Path(self.tmp.name).rglob("*"))
        code, out = run("--posts", self.tmp.name, "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["total"], 3)
        self.assertEqual(sorted((p, p.stat().st_mtime_ns) for p in Path(self.tmp.name).rglob("*")), before)

    def test_missing_folder_exit_2(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(lister.main(["--posts", str(Path(self.tmp.name) / "nope")]), 2)


if __name__ == "__main__":
    unittest.main()
