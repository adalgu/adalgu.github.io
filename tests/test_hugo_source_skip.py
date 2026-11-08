"""BL-003: Notion → Hugo 가져오기는 Source = hugo 쪽(저장소 글의 거울)을 건너뛴다. 가짜 Notion 쪽 JSON, 네트워크 0."""
import os
import tempfile
import unittest

from src.property_mapper import PropertyMapper
from src.render import batch_process_pages

CONFIG = {"filename": {"format": "date-title", "date_format": "%Y-%m-%d", "korean_title": "slug"}}
HAND_POST = "---\ntitle: 손글\nslug: same-slug\ndraft: true\n---\n\n손으로 쓴 새 판\n"


def text(value):
    return [{"type": "text", "plain_text": value, "text": {"content": value}, "annotations": {}}]


def page(page_id, title, source=None, source_type="select", slug="same-slug"):
    props = {
        "Name": {"type": "title", "title": text(title)},
        "Slug": {"type": "rich_text", "rich_text": text(slug)},
        "Date": {"type": "date", "date": {"start": "2026-11-01"}},
        "isPublished": {"type": "checkbox", "checkbox": True},
        "skipRendering": {"type": "checkbox", "checkbox": False},
    }
    if source is not None:
        props["Source"] = ({"type": "select", "select": {"name": source}} if source_type == "select"
                           else {"type": "rich_text", "rich_text": text(source)})
    return {"object": "page", "id": page_id, "archived": False, "properties": props,
            "created_time": "2026-11-01T00:00:00.000Z", "last_edited_time": "2026-11-01T00:00:00.000Z"}


class FakeChildren:
    def __init__(self):
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs.get("block_id"))
        return {"results": [{"type": "paragraph", "id": "b1", "has_children": False,
                             "paragraph": {"rich_text": text("노션 본문")}}], "has_more": False, "next_cursor": None}


class FakeNotion:
    def __init__(self):
        self.blocks = type("Blocks", (), {})()
        self.blocks.children = FakeChildren()


class HugoSourceSkipTests(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(os.chdir, self.cwd)
        os.makedirs("content/posts/same-slug")
        with open("content/posts/same-slug/index.md", "w", encoding="utf-8") as f:
            f.write(HAND_POST)

    def files(self):
        return sorted(os.path.relpath(os.path.join(root, name), "content/posts")
                      for root, _, names in os.walk("content/posts") for name in names)

    def test_source_hugo_page_writes_no_file_and_keeps_hand_post(self):
        notion = FakeNotion()
        result = batch_process_pages([page("p-hugo", "같은 글", "hugo")], notion, {"target_folder": "posts"}, CONFIG)
        self.assertEqual(self.files(), ["same-slug/index.md"])
        self.assertEqual([s["pageId"] for s in result["skipped"]], ["p-hugo"])
        self.assertEqual(notion.blocks.children.calls, [])  # 본문도 안 읽음
        with open("content/posts/same-slug/index.md", encoding="utf-8") as f:
            self.assertEqual(f.read(), HAND_POST)

    def test_other_pages_still_import(self):
        result = batch_process_pages([page("p-notion", "노션 글", slug="notion-only"),
                                      page("p-other", "다른 출처", "notion", slug="other-only")],
                                     FakeNotion(), {"target_folder": "posts"}, CONFIG)
        self.assertEqual(len(result["success"]), 2)
        self.assertEqual(len(self.files()), 3)

    def test_repo_bundle_with_same_slug_or_notion_id_wins(self):
        # BLOG-017 F1: an old Notion-original page (Source notion) whose post now lives in the repo as a bundle
        # must not come back as a flat copy — that is the same URL twice
        with open("content/posts/same-slug/index.md", "w", encoding="utf-8") as f:
            f.write(HAND_POST.replace("draft: true", "draft: false\nnotion_id: 0000aaaa-1111-2222-3333-444455556666"))
        notion = FakeNotion()
        result = batch_process_pages([page("p-moved", "옮긴 글", "notion"),
                                      page("0000aaaa111122223333444455556666", "옮긴 글", "notion", slug="renamed")],
                                     notion, {"target_folder": "posts"}, CONFIG)
        self.assertEqual(self.files(), ["same-slug/index.md"])
        self.assertEqual(len(result["skipped"]), 2)
        self.assertEqual(notion.blocks.children.calls, [])  # skipped before the body is read

    def test_source_match_ignores_case_and_type(self):
        mapper = PropertyMapper()
        self.assertTrue(mapper.should_skip_page({"source": "Hugo"}))
        self.assertTrue(mapper.should_skip_page({"SOURCE": " HUGO "}))
        self.assertFalse(mapper.should_skip_page({"source": "notion"}))
        self.assertFalse(mapper.should_skip_page({"title": "x"}))
        notion = FakeNotion()
        result = batch_process_pages([page("p-rt", "글", "hugo", source_type="rich_text")], notion,
                                     {"target_folder": "posts"}, CONFIG)
        self.assertEqual(len(result["skipped"]), 1)
        self.assertEqual(self.files(), ["same-slug/index.md"])


if __name__ == "__main__":
    unittest.main()
