"""Parse coupon list pages."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from scraper.parse_shoplist import _parse_area_meta, _parse_price


def parse_couponlist(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    coupons: list[dict[str, Any]] = []

    for item in soup.select("li.search_couponlist__item"):
        link = item.select_one("a[href*='/coupon/']")
        title_el = item.select_one("h3")
        text_el = item.select_one(".search_couponlist__text")
        label_el = item.select_one(".search_couponlist__label")
        shop_el = item.select_one(".search_couponlist__shop_name")
        area_el = item.select_one(".search_couponlist__area_genre")
        budget_el = item.select_one(".search_couponlist__budget span")
        hours_el = item.select_one(".search_couponlist__worktime span")

        href = link.get("href", "") if link else ""
        shop_id_match = re.search(r"/shop/(\d+)/", href)

        area_text = area_el.get_text(strip=True) if area_el else ""
        area = _parse_area_meta(area_text.replace("[", "").replace("]", " / ", 1))

        budget_text = budget_el.get_text(" ", strip=True) if budget_el else ""
        hours_text = hours_el.get_text(" ", strip=True) if hours_el else ""

        coupons.append(
            {
                "shop_id": shop_id_match.group(1) if shop_id_match else None,
                "shop_name": shop_el.get_text(strip=True) if shop_el else None,
                "coupon_url": href if href.startswith("http") else f"https://estama.jp{href}",
                "title": title_el.get_text(strip=True) if title_el else None,
                "description": text_el.get_text(" ", strip=True) if text_el else None,
                "label": label_el.get_text(strip=True) if label_el else None,
                "area_raw": area_text,
                **area,
                "price_90min": _parse_price(budget_text),
                "budget_raw": budget_text,
                "hours": hours_text,
            }
        )

    return coupons
