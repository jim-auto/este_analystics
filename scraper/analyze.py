"""Aggregate statistics for customer-facing insights."""

from __future__ import annotations

from collections import Counter
from statistics import median
from typing import Any


def _price_stats(prices: list[int]) -> dict[str, Any]:
    if not prices:
        return {"count": 0, "min": None, "max": None, "median": None, "avg": None}
    return {
        "count": len(prices),
        "min": min(prices),
        "max": max(prices),
        "median": int(median(prices)),
        "avg": int(sum(prices) / len(prices)),
    }


def summarize_shops(shops: list[dict[str, Any]]) -> dict[str, Any]:
    prices = [s["price_90min"] for s in shops if s.get("price_90min")]
    shop_types = Counter(s.get("shop_type") or "不明" for s in shops)
    prefectures = Counter(s.get("prefecture") or "不明" for s in shops)
    sub_areas = Counter(s.get("sub_area") or "不明" for s in shops)

    return {
        "price_90min": _price_stats(prices),
        "available_now_count": sum(1 for s in shops if s.get("available_now")),
        "credit_card_count": sum(1 for s in shops if s.get("credit_card")),
        "with_coupon_count": sum(1 for s in shops if (s.get("coupon_count") or 0) > 0),
        "shop_types": dict(shop_types.most_common(8)),
        "prefectures": dict(prefectures.most_common(10)),
        "top_sub_areas": dict(sub_areas.most_common(10)),
    }


def summarize_rankings(rankings: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, list[dict[str, Any]]] = {}
    for row in rankings:
        by_category.setdefault(row["category"], []).append(row)

    return {
        "categories": list(by_category.keys()),
        "top_by_category": {
            cat: rows[:5] for cat, rows in by_category.items()
        },
        "trend_up_count": sum(1 for r in rankings if r.get("trend") == "up"),
        "trend_down_count": sum(1 for r in rankings if r.get("trend") == "down"),
    }


def summarize_coupons(coupons: list[dict[str, Any]]) -> dict[str, Any]:
    prices = [c["price_90min"] for c in coupons if c.get("price_90min")]
    limited = sum(1 for c in coupons if c.get("label") and "限定" in c["label"])

    return {
        "total": len(coupons),
        "limited_count": limited,
        "price_90min": _price_stats(prices),
        "top_titles": [c["title"] for c in coupons[:8] if c.get("title")],
    }
