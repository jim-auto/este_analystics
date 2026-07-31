"""Cross-source analysis: estama.jp reviews × Bakusai BBS."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from scraper.bbs_analyze import KEYWORD_GROUPS, _find_keywords
from scraper.shop_match import build_shop_matcher, match_shops_in_text

SIGNAL_LABELS = {
    "review_hype_bbs_caution": "公式高評価 × 掲示板注意",
    "review_suspicious_bbs_caution": "注意口コミ × 掲示板注意",
    "review_perfect_bbs_caution": "満点口コミ × 掲示板注意",
    "bbs_buzz_no_reviews": "掲示板のみ言及",
    "aligned_positive": "公式・掲示板とも好評",
    "bbs_caution_only": "掲示板注意のみ",
}


def _index_reviews(reviews: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_shop: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for review in reviews:
        shop_id = review.get("shop_id")
        if shop_id:
            by_shop[str(shop_id)].append(review)
    return by_shop


def _index_bbs_posts(
    posts: list[dict[str, Any]], shop_pairs: list[tuple[str, str]]
) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}

    for post in posts:
        text = post.get("text") or ""
        keywords = _find_keywords(text)
        caution = [k for k in keywords if k in KEYWORD_GROUPS["caution"]]
        positive = [k for k in keywords if k in KEYWORD_GROUPS["positive"]]

        for shop_name in match_shops_in_text(text, shop_pairs=shop_pairs, limit=20):
            entry = details.setdefault(
                shop_name,
                {
                    "mentions": 0,
                    "caution_count": 0,
                    "positive_count": 0,
                    "keywords": [],
                    "excerpts": [],
                },
            )
            entry["mentions"] += 1
            if caution:
                entry["caution_count"] += 1
            if positive:
                entry["positive_count"] += 1
            for kw in keywords:
                if kw not in entry["keywords"]:
                    entry["keywords"].append(kw)
            if (caution or positive) and len(entry["excerpts"]) < 3:
                entry["excerpts"].append(
                    {
                        "text": post.get("excerpt"),
                        "thread_title": post.get("thread_title"),
                        "thread_url": post.get("thread_url"),
                        "flags": caution or positive,
                    }
                )

    return details


def _review_shop_summary(reviews: list[dict[str, Any]], region_median: int | None) -> dict[str, Any]:
    from scraper.review_analyze import _detect_flags

    rated = [r for r in reviews if r.get("rating") is not None]
    suspicious = sum(1 for r in reviews if _detect_flags(r, region_median)[0])
    five_star = sum(1 for r in rated if r.get("rating", 0) >= 5.0)

    return {
        "count": len(reviews),
        "rated_count": len(rated),
        "avg_rating": round(mean(r["rating"] for r in rated), 2) if rated else None,
        "five_star_rate": round(five_star / len(rated) * 100, 1) if rated else None,
        "suspicious_count": suspicious,
    }


def _detect_signals(
    review_summary: dict[str, Any],
    bbs_summary: dict[str, Any] | None,
) -> list[str]:
    signals: list[str] = []
    bbs = bbs_summary or {}
    review_count = review_summary.get("count") or 0
    avg = review_summary.get("avg_rating")
    five_star_rate = review_summary.get("five_star_rate") or 0
    suspicious = review_summary.get("suspicious_count") or 0
    mentions = bbs.get("mentions") or 0
    caution = bbs.get("caution_count") or 0
    positive = bbs.get("positive_count") or 0

    if review_count and avg is not None and avg >= 4.7 and caution >= 1:
        signals.append("review_hype_bbs_caution")
    if suspicious >= 1 and caution >= 1:
        signals.append("review_suspicious_bbs_caution")
    if review_count and five_star_rate >= 100 and caution >= 1:
        signals.append("review_perfect_bbs_caution")
    if mentions >= 1 and review_count == 0:
        signals.append("bbs_buzz_no_reviews")
    if review_count and avg is not None and avg >= 4.3 and positive >= 1 and caution == 0:
        signals.append("aligned_positive")
    if caution >= 1 and review_count == 0:
        signals.append("bbs_caution_only")
    if review_count and five_star_rate >= 75 and caution >= 1:
        if "review_hype_bbs_caution" not in signals:
            signals.append("review_hype_bbs_caution")

    return signals


def build_cross_analysis(
    shops: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    bbs: dict[str, Any],
    region_median: int | None,
) -> dict[str, Any]:
    reviews_by_shop = _index_reviews(reviews)
    posts = bbs.get("posts") or []
    shop_pairs, _ = build_shop_matcher(shops)
    bbs_by_name = _index_bbs_posts(posts, shop_pairs)

    shop_profiles: list[dict[str, Any]] = []
    signal_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for shop in shops:
        shop_id = str(shop["id"])
        shop_reviews = reviews_by_shop.get(shop_id, [])
        review_summary = _review_shop_summary(shop_reviews, region_median)
        bbs_summary = bbs_by_name.get(shop["name"])
        signals = _detect_signals(review_summary, bbs_summary)

        if not shop_reviews and not bbs_summary:
            continue

        profile = {
            "id": shop_id,
            "name": shop["name"],
            "url": shop.get("url"),
            "sub_area": shop.get("sub_area"),
            "price_90min": shop.get("price_90min"),
            "review": review_summary,
            "bbs": bbs_summary,
            "signals": signals,
            "signal_labels": [SIGNAL_LABELS[s] for s in signals if s in SIGNAL_LABELS],
        }
        shop_profiles.append(profile)
        for signal in signals:
            signal_buckets[signal].append(profile)

    for key in signal_buckets:
        signal_buckets[key].sort(
            key=lambda p: (
                (p.get("bbs") or {}).get("caution_count") or 0,
                (p.get("bbs") or {}).get("mentions") or 0,
                p.get("review", {}).get("suspicious_count") or 0,
            ),
            reverse=True,
        )

    matched_shops = len(shop_profiles)
    caution_overlap = (
        len(signal_buckets.get("review_hype_bbs_caution", []))
        + len(signal_buckets.get("review_suspicious_bbs_caution", []))
        + len(signal_buckets.get("review_perfect_bbs_caution", []))
    )

    notes: list[str] = []
    if caution_overlap:
        notes.append(
            f"公式口コミと掲示板の声にギャップがある店舗が{caution_overlap}件見つかりました。"
            "両方の情報源を照合して判断することをおすすめします。"
        )
    if signal_buckets.get("bbs_buzz_no_reviews"):
        notes.append(
            "掲示板でのみ話題になっている店舗があります。"
            "公式口コミサンプルに未登場の可能性があります。"
        )
    if not posts:
        notes.append("掲示板レスのサンプルが不足しているため、クロス分析の精度は限定的です。")

    return {
        "matched_shops": matched_shops,
        "notes": notes,
        "signal_labels": SIGNAL_LABELS,
        "by_signal": {
            key: [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "url": p["url"],
                    "sub_area": p.get("sub_area"),
                    "price_90min": p.get("price_90min"),
                    "review_avg": p.get("review", {}).get("avg_rating"),
                    "review_count": p.get("review", {}).get("count"),
                    "bbs_mentions": (p.get("bbs") or {}).get("mentions"),
                    "bbs_caution": (p.get("bbs") or {}).get("caution_count"),
                    "signal_labels": p.get("signal_labels"),
                }
                for p in profiles[:12]
            ]
            for key, profiles in signal_buckets.items()
        },
        "shops": shop_profiles,
    }


def build_cross_summary(regions: dict[str, dict]) -> dict[str, Any]:
    items = []
    all_gaps = []

    for key, data in regions.items():
        cross = data.get("cross_analysis") or {}
        gap_count = (
            len(cross.get("by_signal", {}).get("review_hype_bbs_caution", []))
            + len(cross.get("by_signal", {}).get("review_suspicious_bbs_caution", []))
            + len(cross.get("by_signal", {}).get("review_perfect_bbs_caution", []))
        )
        items.append(
            {
                "key": key,
                "label": data.get("region_label"),
                "matched_shops": cross.get("matched_shops"),
                "gap_count": gap_count,
                "bbs_buzz_count": len(cross.get("by_signal", {}).get("bbs_buzz_no_reviews", [])),
                "aligned_count": len(cross.get("by_signal", {}).get("aligned_positive", [])),
            }
        )
        for profile in cross.get("by_signal", {}).get("review_hype_bbs_caution", [])[:3]:
            all_gaps.append({**profile, "region_key": key, "region_label": data.get("region_label")})
        for profile in cross.get("by_signal", {}).get("review_suspicious_bbs_caution", [])[:2]:
            all_gaps.append({**profile, "region_key": key, "region_label": data.get("region_label")})
        for profile in cross.get("by_signal", {}).get("review_perfect_bbs_caution", [])[:2]:
            all_gaps.append({**profile, "region_key": key, "region_label": data.get("region_label")})

    return {
        "disclaimer": (
            "公式口コミと掲示板の突合は、サンプル内の店名一致に基づく参考指標です。"
            "表記ゆれ・別店舗・匿名投稿の真偽は検証していません。"
        ),
        "regions": items,
        "top_gaps": all_gaps[:12],
    }
