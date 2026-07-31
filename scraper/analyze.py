"""Aggregate statistics for customer-facing insights."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from statistics import median
from typing import Any

DISCOUNT_RE = re.compile(
    r"(\d{1,3}[,\d]*)\s*円\s*(?:割|OFF|オフ|引)|"
    r"(\d{1,3}[,\d]*)\s*円\s*→|"
    r"(\d{1,3}[,\d]*)\s*円\s*均|"
    r"(\d+)%\s*(?:OFF|オフ)"
)
LATE_NIGHT_RE = re.compile(r"LAST|29:00|30:00|28:00|27:00|26:00|翌|24:00")


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


def _shop_card(shop: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": shop.get("name"),
        "url": shop.get("url"),
        "sub_area": shop.get("sub_area"),
        "prefecture": shop.get("prefecture"),
        "shop_type": shop.get("shop_type"),
        "price_90min": shop.get("price_90min"),
        "hours": shop.get("hours"),
        "credit_card": shop.get("credit_card"),
        "coupon_count": shop.get("coupon_count") or 0,
    }


def _is_late_night(hours: str | None) -> bool:
    if not hours:
        return False
    return bool(LATE_NIGHT_RE.search(hours))


def _price_by_group(
    shops: list[dict[str, Any]], key: str, limit: int = 10
) -> list[dict[str, Any]]:
    groups: dict[str, list[int]] = defaultdict(list)
    counts: Counter[str] = Counter()

    for shop in shops:
        group = shop.get(key) or "不明"
        counts[group] += 1
        if shop.get("price_90min"):
            groups[group].append(shop["price_90min"])

    rows = []
    for name, prices in groups.items():
        if not prices:
            continue
        rows.append(
            {
                "name": name,
                "shop_count": counts[name],
                "price_median": int(median(prices)),
                "price_min": min(prices),
                "price_max": max(prices),
                "priced_shop_count": len(prices),
            }
        )

    rows.sort(key=lambda r: (-r["shop_count"], r["name"]))
    return rows[:limit]


def _parse_discount(text: str) -> int | None:
    if not text:
        return None
    match = DISCOUNT_RE.search(text.replace(" ", ""))
    if not match:
        digits = re.findall(r"(\d{1,3}[,\d]*)円", text.replace(" ", ""))
        for d in digits:
            val = int(d.replace(",", ""))
            if val >= 500:
                return val
        return None
    for group in match.groups():
        if group:
            return int(group.replace(",", ""))
    return None


def _coupon_category(title: str | None, description: str | None) -> str:
    text = f"{title or ''} {description or ''}"
    if any(k in text for k in ("初回", "新規", "はじめて", "初めて")):
        return "初回・新規向け"
    if any(k in text for k in ("リピ", "再来", "リピーター")):
        return "リピーター向け"
    if "指名" in text:
        return "指名料割引"
    if any(k in text for k in ("延長", "時間")):
        return "時間延長"
    return "その他"


def summarize_shops(shops: list[dict[str, Any]]) -> dict[str, Any]:
    prices = [s["price_90min"] for s in shops if s.get("price_90min")]
    shop_types = Counter(s.get("shop_type") or "不明" for s in shops)
    prefectures = Counter(s.get("prefecture") or "不明" for s in shops)
    sub_areas = Counter(s.get("sub_area") or "不明" for s in shops)
    total = len(shops) or 1

    available = [s for s in shops if s.get("available_now")]
    late_night = [s for s in shops if _is_late_night(s.get("hours"))]
    with_coupon = [s for s in shops if (s.get("coupon_count") or 0) > 0]
    credit_card = [s for s in shops if s.get("credit_card")]

    best_value = sorted(
        [s for s in shops if s.get("price_90min") and (s.get("coupon_count") or 0) > 0],
        key=lambda s: s["price_90min"],
    )

    budget_friendly = sorted(
        [s for s in shops if s.get("price_90min")],
        key=lambda s: s["price_90min"],
    )

    return {
        "price_90min": _price_stats(prices),
        "available_now_count": len(available),
        "late_night_count": len(late_night),
        "credit_card_count": len(credit_card),
        "credit_card_rate": round(len(credit_card) / total * 100),
        "with_coupon_count": len(with_coupon),
        "with_coupon_rate": round(len(with_coupon) / total * 100),
        "shop_types": dict(shop_types.most_common(8)),
        "prefectures": dict(prefectures.most_common(10)),
        "top_sub_areas": dict(sub_areas.most_common(10)),
        "price_by_shop_type": _price_by_group(shops, "shop_type", 5),
        "price_by_sub_area": _price_by_group(shops, "sub_area", 12),
        "available_now_shops": [_shop_card(s) for s in available[:20]],
        "late_night_shops": [_shop_card(s) for s in late_night[:12]],
        "best_value_shops": [_shop_card(s) for s in best_value[:12]],
        "budget_friendly_shops": [_shop_card(s) for s in budget_friendly[:12]],
    }


def summarize_rankings(rankings: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, list[dict[str, Any]]] = {}
    for row in rankings:
        by_category.setdefault(row["category"], []).append(row)

    movers_up = [
        {
            "category": r["category"],
            "rank": r["rank"],
            "shop_name": r["shop_name"],
            "shop_url": r["shop_url"],
            "location": r["location"],
        }
        for r in rankings
        if r.get("trend") == "up"
    ]

    return {
        "categories": list(by_category.keys()),
        "top_by_category": {cat: rows[:10] for cat, rows in by_category.items()},
        "trend_up_count": sum(1 for r in rankings if r.get("trend") == "up"),
        "trend_down_count": sum(1 for r in rankings if r.get("trend") == "down"),
        "movers_up": movers_up[:15],
    }


def summarize_coupons(coupons: list[dict[str, Any]]) -> dict[str, Any]:
    prices = [c["price_90min"] for c in coupons if c.get("price_90min")]
    limited = sum(1 for c in coupons if c.get("label") and "限定" in c["label"])

    categories: Counter[str] = Counter()
    enriched = []
    for c in coupons:
        cat = _coupon_category(c.get("title"), c.get("description"))
        categories[cat] += 1
        discount = _parse_discount(f"{c.get('title', '')} {c.get('description', '')}")
        enriched.append({**c, "category": cat, "discount_yen": discount})

    by_discount = sorted(
        [c for c in enriched if c.get("discount_yen")],
        key=lambda c: c["discount_yen"],
        reverse=True,
    )

    return {
        "total": len(coupons),
        "limited_count": limited,
        "price_90min": _price_stats(prices),
        "categories": dict(categories.most_common()),
        "best_discounts": [
            {
                "title": c.get("title"),
                "shop_name": c.get("shop_name"),
                "shop_id": c.get("shop_id"),
                "coupon_url": c.get("coupon_url"),
                "area_raw": c.get("area_raw"),
                "discount_yen": c.get("discount_yen"),
                "price_90min": c.get("price_90min"),
                "category": c.get("category"),
                "description": (c.get("description") or "")[:120],
            }
            for c in by_discount[:15]
        ],
        "by_category": {
            cat: [
                {
                    "title": c.get("title"),
                    "shop_name": c.get("shop_name"),
                    "coupon_url": c.get("coupon_url"),
                    "area_raw": c.get("area_raw"),
                    "price_90min": c.get("price_90min"),
                    "description": (c.get("description") or "")[:100],
                }
                for c in enriched
                if c["category"] == cat
            ][:8]
            for cat in categories
        },
    }


def build_cross_region_highlights(regions: dict[str, dict]) -> dict[str, Any]:
    all_movers = []
    all_discounts = []
    all_budget = []

    for key, data in regions.items():
        label = data["region_label"]
        for m in data["insights"]["rankings"].get("movers_up", []):
            all_movers.append({**m, "region": label, "region_key": key})
        for c in data["insights"]["coupons"].get("best_discounts", []):
            all_discounts.append({**c, "region": label, "region_key": key})
        for s in data["insights"]["shops"].get("budget_friendly_shops", [])[:3]:
            all_budget.append({**s, "region": label, "region_key": key})

    all_discounts.sort(key=lambda c: c.get("discount_yen") or 0, reverse=True)
    all_budget.sort(key=lambda s: s.get("price_90min") or 999999)

    return {
        "ranking_movers": all_movers[:12],
        "best_coupons": all_discounts[:12],
        "budget_picks": all_budget[:9],
    }
