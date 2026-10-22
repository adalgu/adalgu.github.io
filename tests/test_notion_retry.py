"""Offline tests for RetryingClient (mocked HTTP, no Notion calls)."""
import unittest
from unittest import mock

import httpx
from notion_client.errors import APIResponseError

from src.notion_retry import MAX_RETRIES, RetryingClient

RATE_LIMITED = {"object": "error", "status": 429, "code": "rate_limited",
                "message": "You have been rate limited. Please try again later."}


def client_with(responses):
    calls = []

    def handler(request):
        calls.append(request)
        return responses[min(len(calls), len(responses)) - 1]

    return RetryingClient(auth="test", client=httpx.Client(transport=httpx.MockTransport(handler))), calls


class RetryingClientTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("src.notion_retry.time.sleep")
        self.sleep = patcher.start()
        self.addCleanup(patcher.stop)

    def test_retries_429_then_returns_result(self):
        notion, calls = client_with([
            httpx.Response(429, json=RATE_LIMITED, headers={"Retry-After": "3"}),
            httpx.Response(429, json=RATE_LIMITED),
            httpx.Response(200, json={"object": "page", "id": "p1"}),
        ])
        self.assertEqual(notion.pages.retrieve(page_id="p1")["id"], "p1")
        self.assertEqual(len(calls), 3)
        self.assertEqual([c.args[0] for c in self.sleep.call_args_list], [3.0, 2])

    def test_gives_up_after_max_retries(self):
        notion, calls = client_with([httpx.Response(429, json=RATE_LIMITED)])
        with self.assertRaises(APIResponseError):
            notion.pages.retrieve(page_id="p1")
        self.assertEqual(len(calls), MAX_RETRIES + 1)
        self.assertEqual(self.sleep.call_count, MAX_RETRIES)

    def test_wait_is_capped(self):
        notion, _ = client_with([
            httpx.Response(429, json=RATE_LIMITED, headers={"Retry-After": "600"}),
            httpx.Response(200, json={"object": "page", "id": "p1"}),
        ])
        notion.pages.retrieve(page_id="p1")
        self.sleep.assert_called_once_with(60)

    def test_other_errors_are_not_retried(self):
        notion, calls = client_with([httpx.Response(
            404, json={"object": "error", "status": 404, "code": "object_not_found", "message": "x"})])
        with self.assertRaises(APIResponseError):
            notion.pages.retrieve(page_id="p1")
        self.assertEqual(len(calls), 1)
        self.sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
