"""HTTP fetch utilities with polite rate limiting."""

from __future__ import annotations

import time
import urllib.error
import urllib.request

from scraper.config import BASE_URL, REQUEST_DELAY_SEC, USER_AGENT

_last_request_at = 0.0


def fetch_html(path: str) -> str:
    global _last_request_at

    url = path if path.startswith("http") else f"{BASE_URL}{path}"
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
        with urllib.request.urlopen(req, timeout=45) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    finally:
        _last_request_at = time.monotonic()

    return html
