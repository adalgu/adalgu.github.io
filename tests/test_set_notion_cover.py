"""BLOG-011 Notion 쪽 커버 넣기: 가짜 Notion 클라이언트(네트워크 0)로 dry-run 기본·제목 정확히 1쪽·cover만 씀 확인."""
import contextlib
import importlib.util
import io
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "set_notion_cover", Path(__file__).resolve().parent.parent / "scripts" / "set_notion_cover.py")
cover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cover)

TITLES = [title for title, _ in cover.COVERS]


def notion_page(page_id, title, url=None, archived=False):
    page = {"id": page_id, "archived": archived,
            "properties": {"Name": {"type": "title", "title": [{"plain_text": title}]}}}
    if url:
        page["cover"] = {"type": "external", "external": {"url": url}}
    return page


class FakeNotion:
    def __init__(self, pages, title_prop="Name"):
        self.store, self.calls = pages, []
        outer = self

        class Databases:
            def retrieve(self, database_id):
                props = {"Date": {"type": "date"}}
                if title_prop:
                    props[title_prop] = {"type": "title"}
                return {"properties": props}

            def query(self, database_id, filter):
                outer.calls.append(("query", filter))
                want = filter["title"]["equals"]
                return {"results": [p for p in outer.store
                                    if p["properties"][filter["property"]]["title"][0]["plain_text"] == want]}

        class Pages:
            def update(self, page_id, **kwargs):
                outer.calls.append(("update", page_id, kwargs))
                return {"id": page_id}

        self.databases, self.pages = Databases(), Pages()

    def updates(self):
        return [c for c in self.calls if c[0] == "update"]


def run(client, *argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cover.main(["--database", "db-1", *argv], client=client)
    return code, out.getvalue(), err.getvalue()


def three():
    return [notion_page(f"p{i}", title) for i, title in enumerate(TITLES, 1)]


class SetNotionCoverTest(unittest.TestCase):
    def test_table_points_at_site_covers(self):
        self.assertEqual([url for _, url in cover.COVERS], [
            "https://gunn.kim/covers/guanggunje.jpg",
            "https://gunn.kim/covers/github-actions-60day.jpg",
            "https://gunn.kim/covers/github-app-bootstrap.jpg"])
        static = Path(__file__).resolve().parent.parent / "static" / "covers"
        for _, url in cover.COVERS:
            self.assertTrue((static / url.rsplit("/", 1)[1]).is_file(), url)

    def test_dry_run_is_default_and_finds_three(self):
        client = FakeNotion(three())
        code, out, _ = run(client)
        self.assertEqual(code, 0)
        self.assertEqual(client.updates(), [])
        self.assertEqual(out.count("찾음 1쪽"), 3)
        self.assertEqual(out.count("dry-run"), 3)
        for call in client.calls:  # 제목 칸 정확히 일치로만 찾는다
            self.assertEqual(call[1]["property"], "Name")
            self.assertIn(call[1]["title"]["equals"], TITLES)

    def test_apply_writes_cover_only(self):
        client = FakeNotion(three())
        code, _, _ = run(client, "--apply")
        self.assertEqual(code, 0)
        self.assertEqual(client.updates(), [
            ("update", f"p{i}", {"cover": {"type": "external", "external": {"url": url}}})
            for i, (_, url) in enumerate(cover.COVERS, 1)])

    def test_missing_page_stops_before_any_write(self):
        client = FakeNotion(three()[:2])
        code, _, err = run(client, "--apply")
        self.assertEqual(code, 1)
        self.assertEqual(client.updates(), [])
        self.assertIn("멈춤", err)

    def test_two_pages_with_same_title_stop(self):
        client = FakeNotion(three() + [notion_page("dup", TITLES[0])])
        code, out, _ = run(client, "--apply")
        self.assertEqual(code, 1)
        self.assertIn("찾음 2쪽", out)
        self.assertEqual(client.updates(), [])

    def test_archived_duplicate_is_ignored(self):
        client = FakeNotion(three() + [notion_page("old", TITLES[0], archived=True)])
        code, _, _ = run(client, "--apply")
        self.assertEqual(code, 0)
        self.assertEqual(len(client.updates()), 3)

    def test_same_cover_is_skipped(self):
        pages = three()
        pages[0]["cover"] = {"type": "external", "external": {"url": cover.COVERS[0][1]}}
        client = FakeNotion(pages)
        code, out, _ = run(client, "--apply")
        self.assertEqual(code, 0)
        self.assertEqual([c[1] for c in client.updates()], ["p2", "p3"])
        self.assertIn("같음(건너뜀) p1", out)

    def test_single_title_and_url(self):
        client = FakeNotion([notion_page("x1", "다른 글")])
        code, _, _ = run(client, "--title", "다른 글", "--url", "https://gunn.kim/covers/x.jpg", "--apply")
        self.assertEqual(code, 0)
        self.assertEqual(client.updates(), [
            ("update", "x1", {"cover": {"type": "external", "external": {"url": "https://gunn.kim/covers/x.jpg"}}})])

    def test_http_url_and_half_arguments_refused(self):
        client = FakeNotion([notion_page("x1", "다른 글")])
        self.assertEqual(run(client, "--title", "다른 글", "--url", "http://gunn.kim/covers/x.jpg", "--apply")[0], 2)
        self.assertEqual(run(client, "--title", "다른 글")[0], 2)
        self.assertEqual(client.calls, [])

    def test_no_title_column_stops(self):
        client = FakeNotion(three(), title_prop=None)
        self.assertEqual(run(client, "--apply")[0], 2)
        self.assertEqual(client.updates(), [])


if __name__ == "__main__":
    unittest.main()
