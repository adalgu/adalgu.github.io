"""D-20261109-04: Notion 쪽 기본 커버(외부 https 주소)만 Hugo 앞머리 cover로. 가짜 쪽 JSON, 네트워크 0."""
import unittest

from src.property_mapper import PropertyMapper
from src.render import get_page_properties


def text(value):
    return [{"type": "text", "plain_text": value, "text": {"content": value}, "annotations": {}}]


def page(cover=None):
    props = {
        "Name": {"type": "title", "title": text("글 제목")},
        "Date": {"type": "date", "date": {"start": "2026-11-01"}},
        "isPublished": {"type": "checkbox", "checkbox": True},
        "skipRendering": {"type": "checkbox", "checkbox": False},
    }
    p = {"object": "page", "id": "p1", "archived": False, "properties": props,
         "created_time": "2026-11-01T00:00:00.000Z", "last_edited_time": "2026-11-01T00:00:00.000Z"}
    if cover is not None:
        p["cover"] = cover
    return p


def front(p):
    mapper = PropertyMapper()
    return mapper.create_hugo_frontmatter(get_page_properties(p), p)


class NotionCoverTest(unittest.TestCase):
    def test_external_https_cover_becomes_front_matter_cover(self):
        fm = front(page({"type": "external", "external": {"url": "https://gunn.kim/covers/a.jpg"}}))
        self.assertEqual(fm["cover"]["image"], "https://gunn.kim/covers/a.jpg")
        self.assertIs(fm["cover"]["hiddenInSingle"], False)
        self.assertIs(fm["cover"]["hiddenInList"], False)
        self.assertIn("대표 이미지", fm["cover"]["alt"])

    def test_notion_file_cover_is_ignored(self):
        fm = front(page({"type": "file", "file": {"url": "https://prod-files-secure.s3.amazonaws.com/x.png", "expiry_time": "2026-11-09T00:00:00Z"}}))
        self.assertNotIn("cover", fm)

    def test_http_cover_is_ignored(self):
        fm = front(page({"type": "external", "external": {"url": "http://gunn.kim/covers/a.jpg"}}))
        self.assertNotIn("cover", fm)

    def test_no_cover(self):
        self.assertNotIn("cover", front(page()))
        self.assertNotIn("cover", front(page({})))


if __name__ == "__main__":
    unittest.main()
