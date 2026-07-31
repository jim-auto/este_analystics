"""Parse Bakusai thread list and response pages."""

from __future__ import annotations

import html as html_lib
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.bbs_config import BAKUSAI_BASE, BBS_POST_EXCERPT_MAX

TID_RE = re.compile(r"tid=(\d+)")


def _parse_count(text: str) -> int | None:
    raw = text.strip().replace(",", "").replace(" ", "")
    if not raw:
        return None
    if raw.endswith("万"):
        try:
            return int(float(raw[:-1]) * 10000)
        except ValueError:
            return None
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else None


def _clean_post_text(text: str) -> str:
    text = html_lib.unescape(text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _excerpt(text: str, limit: int = BBS_POST_EXCERPT_MAX) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def parse_thread_list(html: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    meta: dict[str, Any] = {}

    title_el = soup.select_one(".countyTitle")
    if title_el:
        meta["board_title"] = title_el.get("title") or title_el.get_text(" ", strip=True)

    threads: list[dict[str, Any]] = []
    for li in soup.select("#thrListInner li"):
        link = li.select_one("a.adult_thr_title")
        if not link:
            continue

        href = link.get("href", "")
        tid_match = TID_RE.search(href)
        if not tid_match:
            continue

        rank_el = li.select_one(".thrNumber")
        content = li.select_one(".thrListContent")
        spans = content.select("span") if content else []

        last_posted = spans[0].get_text(strip=True) if spans else ""
        views = None
        responses = None
        if content:
            view_span = content.select_one(".chart_count_area > span:last-child")
            res_span = content.select_one(".comment_count_area > span:last-child")
            if view_span:
                views = _parse_count(view_span.get_text())
            if res_span:
                responses = _parse_count(res_span.get_text())

        threads.append(
            {
                "tid": tid_match.group(1),
                "rank": int(rank_el.get_text(strip=True)) if rank_el else None,
                "title": link.get("title") or link.get_text(strip=True),
                "url": urljoin(BAKUSAI_BASE, href),
                "last_posted": last_posted,
                "views": views,
                "responses": responses,
            }
        )

    meta["parsed_threads"] = len(threads)
    return threads, meta


def parse_thread_posts(html: str, thread: dict[str, Any]) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[dict[str, Any]] = []

    for article in soup.select("div.article.res_list_article"):
        res_id = article.get("id", "")
        res_num = res_id.replace("res", "") if res_id.startswith("res") else None

        time_el = article.select_one("[itemprop=commentTime]")
        body_el = article.select_one("div.resbody[itemprop=commentText]")
        if not body_el:
            continue

        body = _clean_post_text(body_el.decode_contents())
        if not body:
            continue

        posts.append(
            {
                "res_num": res_num,
                "posted_at": time_el.get_text(strip=True) if time_el else "",
                "text": body,
                "excerpt": _excerpt(body),
                "thread_tid": thread.get("tid"),
                "thread_title": thread.get("title"),
                "thread_url": thread.get("url"),
            }
        )

    return posts


def latest_posts_url(thread_url: str) -> str:
    base = thread_url.rstrip("/")
    if "/tp=1/" in base:
        return f"{base.split('/tp=1/')[0]}/p=1/tp=1/#down"
    return f"{base}/p=1/tp=1/#down"
