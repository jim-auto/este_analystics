"""Review analysis: distribution, keywords, suspicious pattern detection, statistics."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from statistics import mean, median
from typing import Any

from scraper.review_stats import (
    binomial_z_test,
    chi_square_2x2,
    group_mean,
    interpret_correlation,
    pearson_correlation,
    price_tertile_stats,
    shannon_entropy,
    skewness,
    wilson_ci,
)

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

VISIT_LABELS = {
    "first": "初めて",
    "repeat": "2〜4回",
    "loyal": "5回以上",
    "unknown": "不明",
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


def _has_value_keyword(review: dict[str, Any]) -> bool:
    combined = f"{review.get('title', '')} {review.get('text', '')}"
    return any(k in combined for k in VALUE_KEYWORDS)


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


def _compute_statistics(reviews: list[dict[str, Any]], region_median: int | None) -> dict[str, Any]:
    rated = [r for r in reviews if r.get("rating") is not None]
    ratings = [r["rating"] for r in rated]
    five_star_rated = sum(1 for r in rated if r["rating"] >= 5.0)

    dist_counts = [
        sum(1 for r in rated if r["rating"] >= 5.0),
        sum(1 for r in rated if 4.5 <= r["rating"] < 5.0),
        sum(1 for r in rated if 4.0 <= r["rating"] < 4.5),
        sum(1 for r in rated if 3.0 <= r["rating"] < 4.0),
        sum(1 for r in rated if r["rating"] < 3.0),
    ]

    text_lengths = [r.get("text_length", 0) for r in reviews]
    lengths_5 = [r["text_length"] for r in rated if r["rating"] >= 5.0]
    lengths_other = [r["text_length"] for r in rated if r["rating"] < 5.0]

    visit_groups: dict[str, list[float]] = defaultdict(list)
    for r in rated:
        visit_groups[r.get("visit_type") or "unknown"].append(r["rating"])

    visit_stats = {}
    for key, vals in visit_groups.items():
        visit_stats[key] = {
            **group_mean(vals),
            "five_star_rate": round(sum(1 for v in vals if v >= 5.0) / len(vals) * 100, 1),
            "label": VISIT_LABELS.get(key, key),
        }

    with_value = [r for r in rated if _has_value_keyword(r)]
    without_value = [r for r in rated if not _has_value_keyword(r)]

    value_with_perfect = sum(1 for r in with_value if r["rating"] >= 5.0)
    value_without_perfect = len(with_value) - value_with_perfect
    no_value_with_perfect = sum(1 for r in without_value if r["rating"] >= 5.0)
    no_value_without_perfect = len(without_value) - no_value_with_perfect

    price_rating_pairs = [
        (r["price_90min"], r["rating"])
        for r in rated
        if r.get("price_90min") and r.get("rating")
    ]
    prices = [p for p, _ in price_rating_pairs]
    pr_ratings = [r for _, r in price_rating_pairs]
    pearson_r = pearson_correlation(
        [float(p) for p in prices],
        [float(r) for r in pr_ratings],
    )

    shop_ids = Counter(r.get("shop_id") for r in reviews if r.get("shop_id"))
    shop_rating_lists: dict[str, list[float]] = defaultdict(list)
    for r in rated:
        if r.get("shop_id"):
            shop_rating_lists[r["shop_id"]].append(r["rating"])

    all_perfect_shops = sum(
        1 for vals in shop_rating_lists.values() if vals and all(v >= 5.0 for v in vals)
    )
    multi_review_shops = sum(1 for vals in shop_rating_lists.values() if len(vals) >= 2)

    flagged_count = sum(1 for r in reviews if _detect_flags(r, region_median)[0])

    rated_n = len(rated) or 1
    total_n = len(reviews) or 1

    return {
        "sample_size": {
            "reviews": len(reviews),
            "rated": len(rated),
            "unrated": len(reviews) - len(rated),
            "unique_shops": len(shop_ids),
            "avg_reviews_per_shop": round(len(reviews) / max(len(shop_ids), 1), 2),
        },
        "rating_descriptive": {
            **group_mean(ratings),
            "min": min(ratings) if ratings else None,
            "max": max(ratings) if ratings else None,
            "skewness": skewness(ratings),
            "entropy_bits": shannon_entropy(dist_counts),
        },
        "five_star_inference": {
            "rate_pct": round(five_star_rated / rated_n * 100, 1),
            "ci_95_pct": wilson_ci(five_star_rated, len(rated)),
            "vs_neutral_50pct": binomial_z_test(five_star_rated, len(rated), 0.5),
            "vs_benchmark_70pct": binomial_z_test(five_star_rated, len(rated), 0.7),
        },
        "text_length": {
            "all": group_mean([float(x) for x in text_lengths]),
            "rated_5_0": group_mean([float(x) for x in lengths_5]),
            "rated_below_5": group_mean([float(x) for x in lengths_other]),
            "length_gap_5_vs_other": (
                round(mean(lengths_5) - mean(lengths_other), 1)
                if lengths_5 and lengths_other
                else None
            ),
        },
        "visit_type": visit_stats,
        "price_rating": {
            "pearson_r": pearson_r,
            "n": len(price_rating_pairs),
            "interpretation": interpret_correlation(pearson_r),
            "region_median_yen": region_median,
            "by_price_tertile": price_tertile_stats(reviews),
        },
        "value_keyword_effect": {
            "with_keyword": {
                **group_mean([r["rating"] for r in with_value]),
                "five_star_rate": round(
                    sum(1 for r in with_value if r["rating"] >= 5.0) / max(len(with_value), 1) * 100, 1
                ),
            },
            "without_keyword": {
                **group_mean([r["rating"] for r in without_value]),
                "five_star_rate": round(
                    sum(1 for r in without_value if r["rating"] >= 5.0)
                    / max(len(without_value), 1)
                    * 100,
                    1,
                ),
            },
            "perfect_score_chi2": chi_square_2x2(
                value_with_perfect,
                value_without_perfect,
                no_value_with_perfect,
                no_value_without_perfect,
            ),
        },
        "suspicious_inference": {
            "count": flagged_count,
            "rate_pct": round(flagged_count / total_n * 100, 1),
            "ci_95_pct": wilson_ci(flagged_count, total_n),
        },
        "shop_concentration": {
            "shops_with_2plus_reviews": multi_review_shops,
            "shops_all_perfect_in_sample": all_perfect_shops,
            "perfect_shop_rate_pct": round(
                all_perfect_shops / max(len(shop_rating_lists), 1) * 100, 1
            ),
        },
    }


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
    statistics = _compute_statistics(reviews, region_median)

    trust_notes = []
    five_star_rate = round(five_star / rated_count * 100) if rated_count else 0
    if five_star_rate >= 85:
        trust_notes.append(
            f"満点（5.0）が{five_star_rate}%と高く、評価が均一に偏っている可能性があります。"
        )

    fs_test = statistics.get("five_star_inference", {}).get("vs_benchmark_70pct")
    if fs_test and fs_test.get("significant_at_005"):
        trust_notes.append(
            f"満点比率（{fs_test['observed_pct']}%）は中立基準70%より統計的に有意に高い"
            f"（z={fs_test['z_score']}）。"
        )

    skew = statistics.get("rating_descriptive", {}).get("skewness")
    if skew is not None and skew < -0.8:
        trust_notes.append(
            f"評価分布の歪度（{skew}）が負方向に大きく、低評価より高評価へ偏っています。"
        )

    if suspicious_count / total >= 0.08:
        trust_notes.append(
            "割安訴求＋満点など、注意パターンに該当する口コミが一定数見つかりました。"
        )
    if distribution["none"] / total >= 0.25:
        trust_notes.append("評価点数のない口コミが多く、星評価だけでは比較しにくいです。")

    chi2 = statistics.get("value_keyword_effect", {}).get("perfect_score_chi2")
    if chi2 and chi2.get("significant_at_005"):
        trust_notes.append(
            "「割安・コスパ」等の語と満点評価の共起が、偶然以上に見られます（χ²検定 p<0.05）。"
        )

    return {
        "parsed_count": len(reviews),
        "rated_count": len(rated),
        "avg_rating": avg_rating,
        "median_rating": statistics["rating_descriptive"].get("median"),
        "rating_std": statistics["rating_descriptive"].get("std"),
        "five_star_rate": five_star_rate,
        "distribution": distribution,
        "visit_types": dict(visit_types),
        "top_keywords": dict(keyword_counter.most_common(12)),
        "suspicious_count": suspicious_count,
        "suspicious_rate": round(suspicious_count / total * 100, 1),
        "flagged_reviews": flagged[:25],
        "trust_notes": trust_notes,
        "statistics": statistics,
    }


def build_review_summary(regions: dict[str, dict]) -> dict[str, Any]:
    all_flagged = []
    region_stats = []

    for key, data in regions.items():
        insights = data.get("insights", {}).get("reviews", {})
        stats = insights.get("statistics", {})
        for item in insights.get("flagged_reviews", [])[:5]:
            all_flagged.append({**item, "region": data["region_label"], "region_key": key})

        region_stats.append(
            {
                "key": key,
                "label": data["region_label"],
                "avg_rating": insights.get("avg_rating"),
                "median_rating": insights.get("median_rating"),
                "rating_std": insights.get("rating_std"),
                "five_star_rate": insights.get("five_star_rate"),
                "five_star_ci": stats.get("five_star_inference", {}).get("ci_95_pct"),
                "suspicious_rate": insights.get("suspicious_rate"),
                "suspicious_ci": stats.get("suspicious_inference", {}).get("ci_95_pct"),
                "skewness": stats.get("rating_descriptive", {}).get("skewness"),
                "entropy": stats.get("rating_descriptive", {}).get("entropy_bits"),
                "price_correlation": stats.get("price_rating", {}).get("pearson_r"),
                "parsed_count": insights.get("parsed_count"),
                "distribution": insights.get("distribution", {}),
            }
        )

    all_flagged.sort(key=lambda x: -x.get("suspicion_score", 0))

    avgs = [r["avg_rating"] for r in region_stats if r["avg_rating"] is not None]
    cross_notes = []
    if len(avgs) >= 2:
        spread = max(avgs) - min(avgs)
        if spread < 0.15:
            cross_notes.append(f"3エリアの平均評価差は{spread:.2f}点と小さく、エリア間差は限定的です。")
        else:
            cross_notes.append(f"3エリアの平均評価差は最大{spread:.2f}点あります。")

    five_rates = [r["five_star_rate"] for r in region_stats if r["five_star_rate"] is not None]
    if five_rates and max(five_rates) - min(five_rates) >= 10:
        cross_notes.append(
            f"満点比率は{min(five_rates)}%〜{max(five_rates)}%とエリア間で{max(five_rates)-min(five_rates)}pt差があります。"
        )

    return {
        "regions": region_stats,
        "cross_region_notes": cross_notes,
        "top_suspicious": all_flagged[:15],
    }
