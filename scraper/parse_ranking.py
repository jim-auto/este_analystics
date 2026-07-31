"""Parse ranking pages."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup


def _parse_trend(li) -> str:
    trend_el = li.select_one(".ranking_list__compared")
    if not trend_el:
        return "same"
    classes = trend_el.get("class", [])
    if "rank_up" in classes:
        return "up"
    if "rank_down" in classes:
        return "down"
    return "same"


def _parse_rank(li) -> int | None:
    badge = li.select_one(".ranking_list__badge i")
    if not badge:
        return None
    digits = re.sub(r"[^\d]", "", badge.get_text())
    return int(digits) if digits else None


def parse_ranking(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rankings: list[dict[str, Any]] = []

    for column in soup.select(".ranking-column"):
        heading = column.select_one("h2")
        if not heading:
            continue
        category = heading.get_text(strip=True)

        for li in column.select("ul.shop_list > li"):
            name_el = li.select_one(".shop_name a")
            if not name_el:
                continue
            href = name_el.get("href", "")
            shop_id_match = re.search(r"/shop/(\d+)/", href)
            pref_el = li.select_one(".pref_genre")

            rankings.append(
                {
                    "category": category,
                    "rank": _parse_rank(li),
                    "trend": _parse_trend(li),
                    "shop_id": shop_id_match.group(1) if shop_id_match else None,
                    "shop_name": name_el.get_text(strip=True),
                    "shop_url": href if href.startswith("http") else f"https://estama.jp{href}",
                    "location": pref_el.get_text(strip=True) if pref_el else None,
                }
            )

    return rankings
