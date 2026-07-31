"""HTTP fetch utilities with polite rate limiting."""

from __future__ import annotations

import time
import urllib.error
import urllib.request

from scraper.config import BASE_URL, REQUEST_DELAY_SEC, USER_AGENT

_last_request_at = 0.0
MAX_RETRIES = 3


def fetch_html(path: str, *, base_url: str | None = None) -> str:
    global _last_request_at

    if path.startswith("http"):
        url = path
    else:
        root = base_url or BASE_URL
        url = f"{root}{path}"

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        elapsed = time.monotonic() - _last_request_at
        if elapsed < REQUEST_DELAY_SEC:
            time.sleep(REQUEST_DELAY_SEC - elapsed)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ja,en;q=0.8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            _last_request_at = time.monotonic()
            return html
        except urllib.error.HTTPError as exc:
            _last_request_at = time.monotonic()
            raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            _last_request_at = time.monotonic()
            last_error = exc
            if attempt + 1 < MAX_RETRIES:
                time.sleep(3 * (attempt + 1))
                continue
            break

    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts") from last_error
