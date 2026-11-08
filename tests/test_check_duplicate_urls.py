"""BLOG-017 F1: two published pages at one URL fail the build; one each passes. Real hugo when it is installed."""
import contextlib
import importlib.util
import io
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("check_duplicate_urls", ROOT / "scripts" / "check_duplicate_urls.py")
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)

HEAD = "path,slug,title,date,expiryDate,publishDate,draft,permalink,kind,section\n"


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = check.main(list(argv))
    return code, out.getvalue() + err.getvalue()


class DuplicateUrlTests(unittest.TestCase):
    def listing(self, rows):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
        tmp.write(HEAD + "".join(rows))
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return tmp.name

    def test_same_url_twice_fails(self):
        path = self.listing([
            "content/posts/a.md,a,A,,,,false,https://gunn.kim/posts/a/,page,posts\n",
            "content/posts/a/index.md,a,A,,,,false,https://gunn.kim/posts/a/,page,posts\n",
            "content/posts/b/index.md,b,B,,,,false,https://gunn.kim/posts/b/,page,posts\n"])
        code, text = run("--csv", path)
        self.assertEqual(code, 1)
        self.assertIn("2 pages at https://gunn.kim/posts/a/", text)

    def test_every_url_once_passes(self):
        path = self.listing(["content/posts/a/index.md,a,A,,,,false,https://gunn.kim/posts/a/,page,posts\n",
                             "content/posts/b/index.md,b,B,,,,false,https://gunn.kim/posts/b/,page,posts\n"])
        self.assertEqual(run("--csv", path)[0], 0)

    @unittest.skipUnless(shutil.which("hugo"), "hugo not installed")
    def test_real_hugo_flat_copy_next_to_bundle(self):
        # Anton's reproduce.py shape: an old flat Notion copy and the repo bundle with the same slug
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "hugo.yaml").write_text("baseURL: https://example.com/\n")
            post = "---\ntitle: same\nslug: same-slug\ndate: 2026-11-01\ndraft: false\n---\n\nbody\n"
            (site / "content/posts/same-slug").mkdir(parents=True)
            (site / "content/posts/same-slug/index.md").write_text(post)
            self.assertEqual(run("--hugo", "hugo", "--source", str(site))[0], 0)
            (site / "content/posts/2026-11-01-same.md").write_text(post)
            code, text = run("--hugo", "hugo", "--source", str(site))
            self.assertEqual(code, 1)
            self.assertIn("2 pages at https://example.com/posts/same-slug/", text)


if __name__ == "__main__":
    unittest.main()
