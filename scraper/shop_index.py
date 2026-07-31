"""Build per-shop index for detail pages."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def _ranking_by_shop(rankings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_shop: dict[str, dict[str, Any]] = {}
    for row in rankings:
        shop_id = row.get("shop_id")
        if not shop_id:
            continue
        entry = by_shop.setdefault(
            str(shop_id),
            {"categories": [], "best_rank": None, "entries": []},
        )
        entry["categories"].append(row.get("category"))
        entry["entries"].append(
            {
                "category": row.get("category"),
                "rank": row.get("rank"),
                "trend": row.get("trend"),
            }
        )
        rank = row.get("rank")
        if rank and (entry["best_rank"] is None or rank < entry["best_rank"]):
            entry["best_rank"] = rank
    return by_shop


def _coupons_by_shop(coupons: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_shop: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for coupon in coupons:
        shop_id = coupon.get("shop_id")
        if not shop_id:
            continue
        by_shop[str(shop_id)].append(
            {
                "title": coupon.get("title"),
                "coupon_url": coupon.get("coupon_url"),
                "description": (coupon.get("description") or "")[:100],
                "price_90min": coupon.get("price_90min"),
            }
        )
    return dict(by_shop)


def build_shop_index(
    region_key: str,
    region_label: str,
    shops: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    cross_analysis: dict[str, Any],
    rankings: list[dict[str, Any]],
    coupons: list[dict[str, Any]],
) -> dict[str, Any]:
    cross_by_id = {p["id"]: p for p in cross_analysis.get("shops", [])}
    reviews_by_shop: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for review in reviews:
        shop_id = review.get("shop_id")
        if shop_id:
            reviews_by_shop[str(shop_id)].append(
                {
                    "review_id": review.get("review_id"),
                    "rating": review.get("rating"),
                    "title": review.get("title"),
                    "excerpt": (review.get("text") or "")[:160],
                    "date_text": review.get("date_text"),
                    "visit_type": review.get("visit_type"),
                    "review_url": review.get("review_url"),
                }
            )

    ranking_map = _ranking_by_shop(rankings)
    coupon_map = _coupons_by_shop(coupons)

    entries: list[dict[str, Any]] = []
    for shop in shops:
        shop_id = str(shop["id"])
        cross = cross_by_id.get(shop_id)
        shop_reviews = reviews_by_shop.get(shop_id, [])
        ranking = ranking_map.get(shop_id)
        shop_coupons = coupon_map.get(shop_id, [])

        if not cross and not shop_reviews and not ranking and not shop_coupons:
            continue

        entries.append(
            {
                "id": shop_id,
                "name": shop["name"],
                "url": shop.get("url"),
                "sub_area": shop.get("sub_area"),
                "prefecture": shop.get("prefecture"),
                "shop_type": shop.get("shop_type"),
                "price_90min": shop.get("price_90min"),
                "hours": shop.get("hours"),
                "credit_card": shop.get("credit_card"),
                "coupon_count": shop.get("coupon_count"),
                "available_now": shop.get("available_now"),
                "review": cross.get("review") if cross else None,
                "reviews": shop_reviews[:5],
                "bbs": cross.get("bbs") if cross else None,
                "signals": cross.get("signals", []) if cross else [],
                "signal_labels": cross.get("signal_labels", []) if cross else [],
                "ranking": ranking,
                "coupons": shop_coupons[:5],
            }
        )

    entries.sort(
        key=lambda e: (
            len(e.get("signals") or []),
            (e.get("bbs") or {}).get("mentions") or 0,
            (e.get("review") or {}).get("count") or 0,
            -(e.get("price_90min") or 999999),
        ),
        reverse=True,
    )

    return {
        "region_key": region_key,
        "region_label": region_label,
        "shop_count": len(entries),
        "shops": entries,
    }
