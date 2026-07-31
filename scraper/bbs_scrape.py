"""Scrape Bakusai boards for a region."""

from __future__ import annotations

from typing import Any

from scraper.bbs_analyze import analyze_bbs
from scraper.bbs_config import (
    BAKUSAI_BASE,
    BBS_BOARD_SETS,
    BBS_MAX_POSTS_PER_THREAD,
    BBS_SAMPLE_THREADS_PER_BOARD,
    BBS_THREAD_LIST_PAGES,
    board_list_url,
)
from scraper.fetch import fetch_html
from scraper.parse_bakusai import latest_posts_url, parse_thread_list, parse_thread_posts


def _scrape_board(
    board: dict[str, object],
    shop_names: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    acode = int(board["acode"])
    bid = int(board["bid"])
    board_url = board_list_url(acode, bid)

    threads: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"board_label": board["label"], "board_url": board_url}
    for page in range(1, BBS_THREAD_LIST_PAGES + 1):
        html = fetch_html(board_list_url(acode, bid, page), base_url=BAKUSAI_BASE)
        page_threads, page_meta = parse_thread_list(html)
        for t in page_threads:
            t["board_label"] = board["label"]
        threads.extend(page_threads)
        meta.update(page_meta)

    sample_threads = sorted(
        threads,
        key=lambda t: (t.get("responses") or 0, t.get("views") or 0),
        reverse=True,
    )[:BBS_SAMPLE_THREADS_PER_BOARD]

    posts: list[dict[str, Any]] = []
    for thread in sample_threads:
        posts_url = latest_posts_url(thread["url"])
        html = fetch_html(posts_url, base_url=BAKUSAI_BASE)
        page_posts = parse_thread_posts(html, thread)
        posts.extend(page_posts[:BBS_MAX_POSTS_PER_THREAD])

    meta["parsed_threads"] = len(threads)
    meta["sampled_posts"] = len(posts)
    return threads, posts, meta


def scrape_bbs(region_key: str, shop_names: list[str]) -> dict[str, Any]:
    boards = BBS_BOARD_SETS[region_key]
    all_threads: list[dict[str, Any]] = []
    all_posts: list[dict[str, Any]] = []
    board_metas: list[dict[str, Any]] = []

    for board in boards:
        threads, posts, meta = _scrape_board(board, shop_names)
        all_threads.extend(threads)
        all_posts.extend(posts)
        board_metas.append(meta)

    insights = analyze_bbs(all_threads, all_posts, shop_names)
    primary = boards[0]

    return {
        "source": "bakusai.com",
        "source_label": "爆サイ.com（2ch系掲示板）",
        "board": {
            "label": primary["label"],
            "url": board_list_url(int(primary["acode"]), int(primary["bid"])),
            "acode": primary["acode"],
            "bid": primary["bid"],
        },
        "boards_scraped": board_metas,
        "meta": {
            "parsed_threads": len(all_threads),
            "parsed_posts": len(all_posts),
            "board_count": len(boards),
        },
        "threads": all_threads[:40],
        "sample_threads": sorted(
            all_threads,
            key=lambda t: (t.get("responses") or 0, t.get("views") or 0),
            reverse=True,
        )[:10],
        "insights": insights,
        "posts": [
            {
                "text": p.get("text"),
                "excerpt": p.get("excerpt"),
                "thread_title": p.get("thread_title"),
                "thread_url": p.get("thread_url"),
            }
            for p in all_posts
        ],
    }
