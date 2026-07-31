"""Parse regional review list pages."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from scraper.parse_shoplist import _parse_price

VISIT_RE = re.compile(r"\((初めて|2回～4回|5回以上)\)")
RATING_RE = re.compile(r"^(\d\.\d)$")


def _parse_visit_type(date_text: str) -> str | None:
    match = VISIT_RE.search(date_text)
    if not match:
        return None
    mapping = {"初めて": "first", "2回～4回": "repeat", "5回以上": "loyal"}
    return mapping.get(match.group(1))


def parse_reviewlist(html: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    meta: dict[str, Any] = {}

    total_el = soup.select_one(".pagination-results_total")
    if total_el:
        digits = re.sub(r"[^\d]", "", total_el.get_text())
        if digits:
            meta["shop_count"] = int(digits)

    review_total_el = soup.select_one(".pagination-navi__review-total")
    if review_total_el:
        digits = re.findall(r"[\d,]+", review_total_el.get_text().replace(",", ""))
        if digits:
            meta["review_total_official"] = int(digits[-1])

    reviews: list[dict[str, Any]] = []

    for item in soup.select("li.p-reviewlist-rst__item"):
        shop_name_el = item.select_one(".p-reviewlist-rst__shop-name")
        if not shop_name_el:
            continue

        shop_href = shop_name_el.get("href", "")
        shop_id_match = re.search(r"/shop/(\d+)/", shop_href)
        shop_name = shop_name_el.get_text(strip=True)
        shop_url = shop_href if shop_href.startswith("http") else f"https://estama.jp{shop_href}"

        area_text = ""
        area_el = item.select_one(".p-reviewlist-rst__shop-area")
        if area_el:
            area_text = area_el.get_text(" ", strip=True)

        budget_el = item.select_one(".p-reviewlist-rst__shop-subinfo dd")
        budget_text = budget_el.get_text(" ", strip=True) if budget_el else ""
        price_90min = _parse_price(budget_text)

        for rev in item.select(".p-reviewlist-rst__review"):
            rating = None
            scores = rev.select_one(".cast_review__item__scores")
            if scores:
                for span in scores.select("span"):
                    text = span.get_text(strip=True)
                    if RATING_RE.match(text):
                        rating = float(text)
                        break

            text_el = rev.select_one("p.text")
            body = text_el.get_text("\n", strip=True) if text_el else ""

            title_el = rev.select_one(".review_title")
            title = title_el.get_text(strip=True) if title_el else None

            date_el = rev.select_one(".text_gray.font-size-12")
            date_text = date_el.get_text(" ", strip=True) if date_el else ""

            reviewer_el = rev.select_one(".cast_review__item__member .text_gray")
            reviewer = reviewer_el.get_text(strip=True) if reviewer_el else "匿名"

            review_id_el = rev.select_one("[id^='review_']")
            review_id = review_id_el.get("id", "").replace("review_", "") if review_id_el else None

            link_el = rev.select_one("a.outer-link")
            review_url = ""
            if link_el:
                href = link_el.get("href", "")
                review_url = href if href.startswith("http") else f"https://estama.jp{href}"

            reviews.append(
                {
                    "review_id": review_id,
                    "shop_id": shop_id_match.group(1) if shop_id_match else None,
                    "shop_name": shop_name,
                    "shop_url": shop_url,
                    "shop_area": area_text,
                    "price_90min": price_90min,
                    "rating": rating,
                    "title": title,
                    "text": body,
                    "text_length": len(body),
                    "date_text": date_text,
                    "visit_type": _parse_visit_type(date_text),
                    "reviewer_label": reviewer,
                    "review_url": review_url,
                }
            )

    meta["parsed_reviews"] = len(reviews)
    return reviews, meta
