"""Scrape Bakusai boards for a region."""

from __future__ import annotations

from typing import Any

from scraper.bbs_analyze import analyze_bbs
from scraper.bbs_config import (
    BAKUSAI_BASE,
    BBS_BOARDS,
    BBS_MAX_POSTS_PER_THREAD,
    BBS_SAMPLE_THREADS,
    BBS_THREAD_LIST_PAGES,
    board_list_url,
)
from scraper.fetch import fetch_html
from scraper.parse_bakusai import latest_posts_url, parse_thread_list, parse_thread_posts


def scrape_bbs(region_key: str, shop_names: list[str]) -> dict[str, Any]:
    board = BBS_BOARDS[region_key]
    board_url = board_list_url(region_key)

    threads: list[dict[str, Any]] = []
    meta: dict[str, Any] = {}
    for page in range(1, BBS_THREAD_LIST_PAGES + 1):
        html = fetch_html(board_list_url(region_key, page), base_url=BAKUSAI_BASE)
        page_threads, page_meta = parse_thread_list(html)
        threads.extend(page_threads)
        meta.update(page_meta)

    sample_threads = sorted(
        threads,
        key=lambda t: (t.get("responses") or 0, t.get("views") or 0),
        reverse=True,
    )[:BBS_SAMPLE_THREADS]

    posts: list[dict[str, Any]] = []
    for thread in sample_threads:
        posts_url = latest_posts_url(thread["url"])
        html = fetch_html(posts_url, base_url=BAKUSAI_BASE)
        page_posts = parse_thread_posts(html, thread)
        posts.extend(page_posts[:BBS_MAX_POSTS_PER_THREAD])

    insights = analyze_bbs(threads, posts, shop_names)

    return {
        "source": "bakusai.com",
        "source_label": "爆サイ.com（2ch系掲示板）",
        "board": {
            "label": board["label"],
            "url": board_url,
            "acode": board["acode"],
            "bid": board["bid"],
        },
        "meta": meta,
        "threads": threads[:30],
        "sample_threads": [
            {"tid": t["tid"], "title": t["title"], "url": t["url"], "responses": t.get("responses")}
            for t in sample_threads
        ],
        "insights": insights,
    }
