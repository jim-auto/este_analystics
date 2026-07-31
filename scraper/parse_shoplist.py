"""Parse shop list pages."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

PRICE_RE = re.compile(r"90分\s*/\s*[￥¥]?\s*([\d,]+)")


def _parse_price(text: str) -> int | None:
    match = PRICE_RE.search(text.replace(" ", ""))
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _parse_area_meta(text: str) -> dict[str, str | None]:
    parts = [p.strip() for p in text.split("/")]
    prefecture = None
    sub_area = None
    shop_type = None
    nationality = None

    if parts:
        pref_match = re.match(r"\[(.+?)\]", parts[0])
        if pref_match:
            prefecture = pref_match.group(1).strip()
            sub_area = parts[0].split("]", 1)[-1].strip() or None
        else:
            sub_area = parts[0] or None
    if len(parts) > 1:
        shop_type = parts[1].strip() or None
    if len(parts) > 2:
        nationality = parts[2].strip() or None

    return {
        "prefecture": prefecture,
        "sub_area": sub_area,
        "shop_type": shop_type,
        "nationality": nationality,
    }


def parse_shoplist(html: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    meta: dict[str, Any] = {}

    total_el = soup.select_one(".pagination-results_total")
    if total_el:
        digits = re.sub(r"[^\d]", "", total_el.get_text())
        if digits:
            meta["total_shops"] = int(digits)

    range_el = soup.select_one(".pagination-navi_from_to")
    if range_el:
        meta["display_range"] = range_el.get_text(strip=True)

    shops: list[dict[str, Any]] = []
    for item in soup.select("li.shoplist-item"):
        name_el = item.select_one(".shoplist-item_header_shop_name a")
        if not name_el:
            continue

        href = name_el.get("href", "")
        shop_id_match = re.search(r"/shop/(\d+)/", href)
        if not shop_id_match:
            continue

        area_el = item.select_one(".shoplist-item_header_shop_name_wrap p")
        area_text = area_el.get_text(" ", strip=True) if area_el else ""
        area = _parse_area_meta(area_text)

        info = item.select_one(".shoplist-item_body_main_info")
        budget_text = ""
        hours_text = ""
        if info:
            dds = info.select("dd")
            if dds:
                budget_text = dds[0].get_text(" ", strip=True)
            if len(dds) > 1:
                hours_text = dds[1].get_text(" ", strip=True)

        coupon_el = item.select_one('a[href$="/coupon/"] .underline')
        coupon_count = None
        if coupon_el:
            digits = re.sub(r"[^\d]", "", coupon_el.get_text())
            coupon_count = int(digits) if digits else 0

        shops.append(
            {
                "id": shop_id_match.group(1),
                "name": name_el.get_text(strip=True),
                "url": href if href.startswith("http") else f"https://estama.jp{href}",
                **area,
                "price_90min": _parse_price(budget_text),
                "budget_raw": budget_text.replace("\u3000", " ").strip(),
                "hours": hours_text,
                "available_now": item.select_one(".shoplist-item_body_main_boost_st") is not None,
                "credit_card": "カードOK" in budget_text,
                "coupon_count": coupon_count,
            }
        )

    return shops, meta


def parse_shoplist_pages(html_pages: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_shops: list[dict[str, Any]] = []
    meta: dict[str, Any] = {}
    seen: set[str] = set()

    for html in html_pages:
        shops, page_meta = parse_shoplist(html)
        if "total_shops" in page_meta:
            meta["total_shops"] = page_meta["total_shops"]
        for shop in shops:
            if shop["id"] in seen:
                continue
            seen.add(shop["id"])
            all_shops.append(shop)

    meta["sampled_shops"] = len(all_shops)
    return all_shops, meta
