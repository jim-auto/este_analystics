"""Build sub-area index for regional drill-down pages."""

from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any


def build_subarea_index(
    region_key: str,
    region_label: str,
    shops: list[dict[str, Any]],
    shop_index: dict[str, Any],
) -> dict[str, Any]:
    indexed = {s["id"]: s for s in shop_index.get("shops", [])}
    by_area: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for shop in shops:
        area = shop.get("sub_area") or "不明"
        by_area[area].append(shop)

    areas: list[dict[str, Any]] = []
    for name, area_shops in by_area.items():
        if name == "不明" or len(area_shops) < 2:
            continue

        prices = [s["price_90min"] for s in area_shops if s.get("price_90min")]
        available = sum(1 for s in area_shops if s.get("available_now"))
        with_coupon = sum(1 for s in area_shops if (s.get("coupon_count") or 0) > 0)

        signal_shops = []
        for shop in area_shops:
            entry = indexed.get(shop["id"])
            if entry and entry.get("signals"):
                signal_shops.append(
                    {
                        "id": shop["id"],
                        "name": shop["name"],
                        "price_90min": shop.get("price_90min"),
                        "signal_labels": entry.get("signal_labels", []),
                        "review_avg": (entry.get("review") or {}).get("avg_rating"),
                        "bbs_mentions": (entry.get("bbs") or {}).get("mentions"),
                    }
                )

        signal_shops.sort(
            key=lambda s: (len(s.get("signal_labels") or []), s.get("bbs_mentions") or 0),
            reverse=True,
        )

        budget_shops = sorted(
            [s for s in area_shops if s.get("price_90min")],
            key=lambda s: s["price_90min"],
        )[:5]

        areas.append(
            {
                "name": name,
                "shop_count": len(area_shops),
                "priced_count": len(prices),
                "price_median": int(median(prices)) if prices else None,
                "price_min": min(prices) if prices else None,
                "price_max": max(prices) if prices else None,
                "available_now": available,
                "with_coupon": with_coupon,
                "signal_shop_count": len(signal_shops),
                "signal_shops": signal_shops[:8],
                "budget_shops": [
                    {
                        "id": s["id"],
                        "name": s["name"],
                        "price_90min": s.get("price_90min"),
                        "available_now": s.get("available_now"),
                        "coupon_count": s.get("coupon_count"),
                    }
                    for s in budget_shops
                ],
                "shops": [
                    {
                        "id": s["id"],
                        "name": s["name"],
                        "price_90min": s.get("price_90min"),
                        "shop_type": s.get("shop_type"),
                        "available_now": s.get("available_now"),
                        "coupon_count": s.get("coupon_count"),
                        "signals": indexed.get(s["id"], {}).get("signals", []),
                        "signal_labels": indexed.get(s["id"], {}).get("signal_labels", []),
                    }
                    for s in sorted(
                        area_shops,
                        key=lambda x: (
                            len(indexed.get(x["id"], {}).get("signals") or []),
                            x.get("available_now") or False,
                            -(x.get("price_90min") or 999999),
                        ),
                        reverse=True,
                    )[:25]
                ],
            }
        )

    areas.sort(key=lambda a: (-a["shop_count"], a["name"]))

    return {
        "region_key": region_key,
        "region_label": region_label,
        "area_count": len(areas),
        "areas": areas,
    }


def pick_featured_subareas(subarea_index: dict[str, Any], region_key: str) -> list[dict[str, Any]]:
    from scraper.config import FEATURED_SUBAREA_KEYWORDS

    patterns = FEATURED_SUBAREA_KEYWORDS.get(region_key, ())
    areas = subarea_index.get("areas", [])
    picked: list[dict[str, Any]] = []
    used_names: set[str] = set()

    for pattern in patterns:
        for area in areas:
            name = area.get("name", "")
            if pattern in name and name not in used_names:
                picked.append(
                    {
                        "name": name,
                        "price_median": area.get("price_median"),
                        "shop_count": area.get("shop_count"),
                        "signal_shop_count": area.get("signal_shop_count", 0),
                    }
                )
                used_names.add(name)
                break

    return picked[:6]

