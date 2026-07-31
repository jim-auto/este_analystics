"""Review analysis: distribution, keywords, suspicious pattern detection."""

from __future__ import annotations

import re
from collections import Counter
from statistics import mean
from typing import Any

VALUE_KEYWORDS = (
    "割安",
    "激安",
    "コスパ",
    "安い",
    "リーズナブル",
    "お得",
    "破格",
    "安め",
    "買い",
    "穴場",
)
SUPERLATIVES = ("最高", "過最高", "神", "やばい", "マジで", "大満足", "文句なし", "間違いなし")
PRAISE_SHORT = ("最高", "満足", "また行", "リピ", "良かった", "オススメ", "おすすめ")

KEYWORD_TAGS = {
    "コスパ": "コスパ",
    "割安": "割安",
    "激安": "激安",
    "安い": "割安",
    "お得": "お得",
    "最高": "高評価",
    "満足": "満足",
    "癒": "癒し",
    "技術": "施術",
    "マッサージ": "施術",
    "指名": "指名",
    "また": "リピート",
}


def _rating_bucket(rating: float | None) -> str:
    if rating is None:
        return "評価なし"
    if rating >= 5.0:
        return "5.0"
    if rating >= 4.5:
        return "4.5-4.9"
    if rating >= 4.0:
        return "4.0-4.4"
    if rating >= 3.0:
        return "3.0-3.9"
    return "3.0未満"


def _extract_keywords(text: str) -> list[str]:
    found = []
    for key, tag in KEYWORD_TAGS.items():
        if key in text and tag not in found:
            found.append(tag)
    return found


def _detect_flags(review: dict[str, Any], region_median: int | None) -> tuple[list[str], list[str], int]:
    flags: list[str] = []
    reasons: list[str] = []

    text = review.get("text") or ""
    title = review.get("title") or ""
    combined = f"{title} {text}"
    rating = review.get("rating")
    price = review.get("price_90min")

    has_value = any(k in combined for k in VALUE_KEYWORDS)

    if rating == 5.0 and has_value:
        flags.append("value_hype")
        reasons.append("「割安・コスパ・激安」などの訴求＋満点評価")

    if rating == 5.0 and price and region_median and price > region_median * 1.05 and has_value:
        flags.append("price_mismatch")
        reasons.append(
            f"割安系の表現があるが店舗90分料金（¥{price:,}）はエリア中央値（¥{region_median:,}）より高め"
        )

    if rating == 5.0 and review.get("text_length", 0) < 35:
        flags.append("short_perfect")
        reasons.append("非常に短い文章で満点（具体性が少ない）")

    if rating == 5.0 and review.get("visit_type") == "first" and review.get("text_length", 0) < 60:
        flags.append("first_visit_hype")
        reasons.append("初回利用の短文満点（初見での過度な高評価）")

    super_count = sum(1 for s in SUPERLATIVES if s in combined)
    if rating == 5.0 and super_count >= 2:
        flags.append("superlative_stack")
        reasons.append("「最高」「神」など強い褒め言葉が複数")

    if rating == 5.0 and not has_value:
        praise_hits = sum(1 for p in PRAISE_SHORT if p in combined)
        if praise_hits >= 2 and review.get("text_length", 0) < 80:
            flags.append("generic_praise")
            reasons.append("定型的な褒め言葉のみで具体描写が少ない")

    if rating == 5.0 and re.fullmatch(r"[ぁ-んァ-ヶーa-zA-Z0-9！!。.\s]+", text) and len(text) < 20:
        flags.append("minimal_text")
        reasons.append("極端に短いテキストの満点")

    score = len(flags) + (1 if "price_mismatch" in flags else 0)
    return flags, reasons, score


def analyze_reviews(
    reviews: list[dict[str, Any]], region_median: int | None
) -> dict[str, Any]:
    rated = [r for r in reviews if r.get("rating") is not None]
    buckets = Counter(_rating_bucket(r.get("rating")) for r in reviews)

    distribution = {
        "5.0": buckets.get("5.0", 0),
        "4.5-4.9": buckets.get("4.5-4.9", 0),
        "4.0-4.4": buckets.get("4.0-4.4", 0),
        "3.0-3.9": buckets.get("3.0-3.9", 0),
        "below_3": buckets.get("3.0未満", 0),
        "none": buckets.get("評価なし", 0),
    }

    visit_types = Counter(r.get("visit_type") or "unknown" for r in reviews)

    keyword_counter: Counter[str] = Counter()
    for r in reviews:
        for kw in _extract_keywords(f"{r.get('title', '')} {r.get('text', '')}"):
            keyword_counter[kw] += 1

    flagged = []
    for r in reviews:
        flags, reasons, score = _detect_flags(r, region_median)
        if flags:
            flagged.append(
                {
                    "review_id": r.get("review_id"),
                    "shop_name": r.get("shop_name"),
                    "shop_url": r.get("shop_url"),
                    "review_url": r.get("review_url"),
                    "shop_area": r.get("shop_area"),
                    "price_90min": r.get("price_90min"),
                    "rating": r.get("rating"),
                    "title": r.get("title"),
                    "excerpt": (r.get("text") or "")[:160],
                    "date_text": r.get("date_text"),
                    "visit_type": r.get("visit_type"),
                    "flags": flags,
                    "reasons": reasons,
                    "suspicion_score": score,
                }
            )

    flagged.sort(key=lambda x: (-x["suspicion_score"], -(x.get("rating") or 0)))

    total = len(reviews) or 1
    rated_count = len(rated) or 1
    five_star = distribution["5.0"]
    suspicious_count = len(flagged)

    avg_rating = round(mean(r["rating"] for r in rated), 2) if rated else None

    trust_notes = []
    five_star_rate = round(five_star / rated_count * 100) if rated_count else 0
    if five_star_rate >= 85:
        trust_notes.append(
            f"満点（5.0）が{five_star_rate}%と高く、評価が均一に偏っている可能性があります。"
        )
    if suspicious_count / total >= 0.08:
        trust_notes.append(
            "割安訴求＋満点など、注意パターンに該当する口コミが一定数見つかりました。"
        )
    if distribution["none"] / total >= 0.25:
        trust_notes.append("評価点数のない口コミが多く、星評価だけでは比較しにくいです。")

    return {
        "parsed_count": len(reviews),
        "rated_count": len(rated),
        "avg_rating": avg_rating,
        "five_star_rate": five_star_rate,
        "distribution": distribution,
        "visit_types": dict(visit_types),
        "top_keywords": dict(keyword_counter.most_common(12)),
        "suspicious_count": suspicious_count,
        "suspicious_rate": round(suspicious_count / total * 100, 1),
        "flagged_reviews": flagged[:25],
        "trust_notes": trust_notes,
    }


def build_review_summary(regions: dict[str, dict]) -> dict[str, Any]:
    all_flagged = []
    for key, data in regions.items():
        insights = data.get("insights", {}).get("reviews", {})
        for item in insights.get("flagged_reviews", [])[:5]:
            all_flagged.append({**item, "region": data["region_label"], "region_key": key})

    all_flagged.sort(key=lambda x: -x.get("suspicion_score", 0))

    return {
        "regions": [
            {
                "key": key,
                "label": regions[key]["region_label"],
                "avg_rating": regions[key].get("insights", {}).get("reviews", {}).get("avg_rating"),
                "five_star_rate": regions[key].get("insights", {}).get("reviews", {}).get("five_star_rate"),
                "suspicious_rate": regions[key].get("insights", {}).get("reviews", {}).get("suspicious_rate"),
                "distribution": regions[key].get("insights", {}).get("reviews", {}).get("distribution", {}),
                "parsed_count": regions[key].get("review_meta", {}).get("parsed_reviews"),
            }
            for key in regions
        ],
        "top_suspicious": all_flagged[:15],
    }
