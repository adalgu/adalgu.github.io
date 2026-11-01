"""BLOG-010: '글 없음' 막이(scripts/check_flat_posts.sh) — 평평한 글 수 · 손글 묶음은 안 셈 · 직전 성공 대비 50% 미만이면 멈춤."""
import os
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "check_flat_posts.sh")


def run(posts, baseline):
    return subprocess.run([SCRIPT, posts, baseline, "50"], capture_output=True, text=True)


class CheckFlatPosts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.posts = os.path.join(self.tmp.name, "posts")
        os.makedirs(self.posts)
        self.baseline = os.path.join(self.tmp.name, "flat-count")

    def tearDown(self):
        self.tmp.cleanup()

    def flat(self, n):
        for i in range(n):
            open(os.path.join(self.posts, f"2020-01-{i:04d}-post.md"), "w").write("---\ntitle: t\n---\n")

    def bundle(self):
        os.makedirs(os.path.join(self.posts, "hand-post"))
        open(os.path.join(self.posts, "hand-post", "index.md"), "w").write("---\ntitle: 손글\n---\n")

    def test_flat_zero_with_hand_bundle_stops(self):  # (a)
        self.bundle()
        open(os.path.join(self.posts, "_index.md"), "w").write("---\n---\n")
        self.assertEqual(run(self.posts, self.baseline).returncode, 1)
        self.assertFalse(os.path.exists(self.baseline))

    def test_normal_60_passes_and_records_count(self):  # (b)
        self.bundle()
        self.flat(60)
        self.assertEqual(run(self.posts, self.baseline).returncode, 0)
        self.assertEqual(open(self.baseline).read().strip(), "60")

    def test_drop_below_half_stops_and_keeps_baseline(self):  # (c)
        open(self.baseline, "w").write("60\n")
        self.flat(29)
        self.assertEqual(run(self.posts, self.baseline).returncode, 1)
        self.assertEqual(open(self.baseline).read().strip(), "60")

    def test_exactly_half_passes(self):
        open(self.baseline, "w").write("60\n")
        self.flat(30)
        self.assertEqual(run(self.posts, self.baseline).returncode, 0)
        self.assertEqual(open(self.baseline).read().strip(), "30")

    def test_first_run_without_baseline_only_blocks_zero(self):
        self.flat(3)
        self.assertEqual(run(self.posts, self.baseline).returncode, 0)

    def test_missing_dir_stops(self):
        self.assertEqual(run(os.path.join(self.tmp.name, "nope"), self.baseline).returncode, 1)


if __name__ == "__main__":
    unittest.main()
