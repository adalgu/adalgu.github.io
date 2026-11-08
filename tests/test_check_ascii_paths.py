"""BLOG-017 addendum 5: a non-ASCII path under content/ fails; the real repo passes; the rename keeps the URL."""
import contextlib
import importlib.util
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = load("check_ascii_paths")
rename = load("ascii_bundle_folders")


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


class AsciiPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        folder = self.repo / "content/posts/스몰토크는-왜-중요한가"
        folder.mkdir(parents=True)
        (folder / "index.md").write_text("---\ndate: '2026-05-15'\nnotion_id: 3617522e-eb2f-805c\n"
                                         "slug: \"스몰토크는-왜-중요한가\"\ntitle: t\n---\n\nbody\n", encoding="utf-8")
        (folder / "image-01.png").write_bytes(b"png")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "korean")

    def test_korean_folder_fails(self):
        self.assertEqual(quiet(check.main, ["--repo", str(self.repo)]), 1)

    def test_rename_then_passes_and_keeps_the_url(self):
        self.assertEqual(quiet(rename.main, ["--repo", str(self.repo), "--apply"]), 0)
        self.assertEqual(quiet(check.main, ["--repo", str(self.repo)]), 0)
        index = (self.repo / "content/posts/post-20260515-3617522e/index.md").read_text(encoding="utf-8")
        self.assertIn('url: "/posts/스몰토크는-왜-중요한가/"', index)
        self.assertNotIn("slug:", index)
        self.assertTrue((self.repo / "content/posts/post-20260515-3617522e/image-01.png").is_file())
        self.assertEqual(quiet(rename.main, ["--repo", str(self.repo), "--apply"]), 0)  # nothing left to do

    def test_untracked_and_build_time_files_count_too(self):
        # Anton round 5 P2: git's list missed a file the build writes (leftover import) — the check walks the tree
        quiet(rename.main, ["--repo", str(self.repo), "--apply"])
        self.assertEqual(quiet(check.main, ["--repo", str(self.repo)]), 0)
        (self.repo / "content/posts/2026-11-09-새-글.md").write_text("flat\n", encoding="utf-8")  # never git-added
        self.assertEqual(quiet(check.main, ["--repo", str(self.repo)]), 1)

    def test_this_repo_is_all_ascii(self):
        self.assertEqual(quiet(check.main, ["--repo", str(ROOT)]), 0)


if __name__ == "__main__":
    unittest.main()
