"""Notion client that waits and retries when the API rate-limits (HTTP 429)."""
import time

from notion_client import Client
from notion_client.errors import HTTPResponseError

MAX_RETRIES = 5
MAX_WAIT_SECONDS = 60


class RetryingClient(Client):
    """Client whose every API call retries on 429, honoring Retry-After."""

    def request(self, *args, **kwargs):
        for attempt in range(MAX_RETRIES + 1):
            try:
                return super().request(*args, **kwargs)
            except HTTPResponseError as error:
                if error.status != 429 or attempt == MAX_RETRIES:
                    raise
                try:
                    wait = float(error.headers.get("retry-after", ""))
                except ValueError:
                    wait = 2 ** attempt
                wait = min(wait, MAX_WAIT_SECONDS)
                print(f"[Warning] Notion rate limited; retry {attempt + 1}/{MAX_RETRIES} in {wait:.0f}s")
                time.sleep(wait)
