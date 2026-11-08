"""BLOG-017 addendum 3 (Anton round 4): ad shortcodes draw nothing while their params are unset or YOUR_…
placeholders (a placeholder unit made googleads answer 400 -> console errors -> site_check red)."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHORTCODES = ("adsense", "adsense2", "adfit")
POST = "---\ntitle: ad\nslug: ad\ndate: 2026-11-01\ndraft: false\n---\n\nbefore\n\n{{< adsense >}}\n\n{{< adsense2 >}}\n\n{{< adfit >}}\n\nafter\n"


@unittest.skipUnless(shutil.which("hugo"), "hugo not installed")
class AdShortcodeTests(unittest.TestCase):
    def build(self, params):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "layouts/shortcodes").mkdir(parents=True)
            (site / "layouts/_default").mkdir(parents=True)
            (site / "layouts/_default/single.html").write_text("{{ .Content }}")
            for name in SHORTCODES:
                shutil.copy(ROOT / "layouts/shortcodes" / f"{name}.html", site / "layouts/shortcodes")
            (site / "hugo.yaml").write_text("baseURL: https://example.com/\nparams:\n" + params)
            (site / "content/posts").mkdir(parents=True)
            (site / "content/posts/ad.md").write_text(POST)
            subprocess.run(["hugo", "--source", str(site), "--quiet"], check=True, capture_output=True)
            return (site / "public/posts/ad/index.html").read_text()

    def test_unset_params_draw_nothing(self):
        html = self.build("  description: x\n")
        self.assertNotIn("adsbygoogle", html)
        self.assertNotIn("kakao_ad_area", html)
        self.assertIn("before", html)
        self.assertIn("after", html)

    def test_placeholders_draw_nothing(self):
        html = self.build("  adsense:\n    client: ca-pub-YOUR_AD_CLIENT_ID\n    slot: YOUR_AD_SLOT\n"
                          "  adfit:\n    unit: YOUR_AD_UNIT\n")
        self.assertNotIn("YOUR_AD", html)
        self.assertNotIn("adsbygoogle", html)
        self.assertNotIn("kakao_ad_area", html)

    def test_client_without_slot_draws_nothing(self):
        self.assertNotIn("adsbygoogle", self.build("  adsense:\n    client: ca-pub-1234567890\n"))

    def test_real_values_draw_the_unit(self):
        html = self.build("  adsense:\n    client: ca-pub-1234567890\n    slot: '9876543210'\n  adfit:\n    unit: DAN-abc123\n")
        self.assertEqual(html.count('data-ad-slot="9876543210"'), 2)  # adsense + adsense2
        self.assertIn('data-ad-client="ca-pub-1234567890"', html)
        self.assertIn('data-ad-unit="DAN-abc123"', html)

    def test_site_build_has_no_ad_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["hugo", "--source", str(ROOT), "--destination", tmp, "--quiet", "--minify",
                            "--baseURL", "https://gunn.kim/"], check=True, capture_output=True)
            hits = [p for p in Path(tmp).rglob("*.html") if "YOUR_AD" in p.read_text(errors="ignore")]
            self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
