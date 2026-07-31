"""Main scraper entry point."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scraper.analyze import (
    build_cross_region_highlights,
    summarize_coupons,
    summarize_rankings,
    summarize_shops,
)
from scraper.bbs_analyze import build_bbs_summary
from scraper.bbs_scrape import scrape_bbs
from scraper.config import REGIONS, REVIEWLIST_PAGES, SHOPLIST_MAX_PAGES
from scraper.cross_analyze import build_cross_analysis, build_cross_summary
from scraper.fetch import fetch_html
from scraper.parse_couponlist import parse_couponlist
from scraper.parse_ranking import parse_ranking
from scraper.parse_reviewlist import parse_reviewlist
from scraper.parse_shoplist import parse_shoplist_pages
from scraper.review_analyze import analyze_reviews, build_review_summary
from scraper.shop_index import build_shop_index

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DATA_DIR = ROOT / "docs" / "data"


def _shoplist_paths(slug: str) -> list[str]:
    paths = [f"/{slug}/shoplist/"]
    for page in range(2, SHOPLIST_MAX_PAGES + 1):
        paths.append(f"/{slug}/shoplist/p{page}/")
    return paths


def scrape_region(key: str) -> tuple[dict, dict]:
    cfg = REGIONS[key]
    slug = cfg["slug"]

    print(f"[{cfg['label']}] fetching rankings...")
    rankings = parse_ranking(fetch_html(f"/{slug}/ranking/"))

    print(f"[{cfg['label']}] fetching coupons...")
    coupons = parse_couponlist(fetch_html(f"/{slug}/couponlist/"))

    print(f"[{cfg['label']}] fetching shoplist ({SHOPLIST_MAX_PAGES} pages)...")
    shop_pages = [fetch_html(path) for path in _shoplist_paths(slug)]
    shops, shop_meta = parse_shoplist_pages(shop_pages)

    print(f"[{cfg['label']}] fetching reviews...")
    review_pages = [
        fetch_html(f"/{slug}/reviewlist/" if p == 1 else f"/{slug}/reviewlist/p{p}/")
        for p in range(1, REVIEWLIST_PAGES + 1)
    ]
    reviews: list = []
    review_meta: dict = {}
    for html in review_pages:
        page_reviews, page_meta = parse_reviewlist(html)
        reviews.extend(page_reviews)
        review_meta.update(page_meta)
    review_meta["parsed_reviews"] = len(reviews)

    shop_insights = summarize_shops(shops)
    region_median = shop_insights["price_90min"].get("median")

    print(f"[{cfg['label']}] fetching BBS (bakusai)...")
    shop_names = [s["name"] for s in shops if s.get("name")]
    bbs = scrape_bbs(key, shop_names)

    cross_analysis = build_cross_analysis(shops, reviews, bbs, region_median)
    shop_index = build_shop_index(
        key,
        cfg["label"],
        shops,
        reviews,
        cross_analysis,
        rankings,
        coupons,
    )

    bbs_public = {k: v for k, v in bbs.items() if k != "posts"}

    return {
        "region_key": key,
        "region_label": cfg["label"],
        "region_subtitle": cfg["subtitle"],
        "region_description": cfg["description"],
        "source_urls": {
            "ranking": f"https://estama.jp/{slug}/ranking/",
            "coupons": f"https://estama.jp/{slug}/couponlist/",
            "shoplist": f"https://estama.jp/{slug}/shoplist/",
            "reviews": f"https://estama.jp/{slug}/reviewlist/",
        },
        "shop_meta": shop_meta,
        "review_meta": review_meta,
        "rankings": rankings,
        "coupons": coupons,
        "insights": {
            "shops": shop_insights,
            "rankings": summarize_rankings(rankings),
            "coupons": summarize_coupons(coupons),
            "reviews": analyze_reviews(reviews, region_median),
        },
        "bbs": bbs_public,
        "cross_analysis": {
            "matched_shops": cross_analysis.get("matched_shops"),
            "notes": cross_analysis.get("notes"),
            "signal_labels": cross_analysis.get("signal_labels"),
            "by_signal": cross_analysis.get("by_signal"),
        },
    }, shop_index


def build_summary(regions: dict[str, dict], updated_at: str) -> dict:
    shop_insights = {key: regions[key]["insights"]["shops"] for key in REGIONS}
    return {
        "updated_at": updated_at,
        "disclaimer": (
            "本サイトはエステ魂（estama.jp）の公開情報を分析・再整理した非公式サイトです。"
            "予約・最新情報は公式サイトをご確認ください。"
        ),
        "source": "https://estama.jp/",
        "highlights": build_cross_region_highlights(regions),
        "reviews": build_review_summary(regions),
        "bbs": build_bbs_summary(regions),
        "cross": build_cross_summary(regions),
        "regions": [
            {
                "key": key,
                "label": REGIONS[key]["label"],
                "subtitle": REGIONS[key]["subtitle"],
                "total_shops": regions[key]["shop_meta"].get("total_shops"),
                "sampled_shops": regions[key]["shop_meta"].get("sampled_shops"),
                "coupon_count": len(regions[key]["coupons"]),
                "price_median": shop_insights[key]["price_90min"]["median"],
                "price_min": shop_insights[key]["price_90min"]["min"],
                "price_max": shop_insights[key]["price_90min"]["max"],
                "available_now": shop_insights[key]["available_now_count"],
                "late_night": shop_insights[key]["late_night_count"],
                "credit_card_rate": shop_insights[key]["credit_card_rate"],
                "with_coupon_rate": shop_insights[key]["with_coupon_rate"],
                "price_by_shop_type": shop_insights[key]["price_by_shop_type"],
                "top_sub_areas": shop_insights[key]["price_by_sub_area"][:5],
                "review_avg": regions[key]["insights"]["reviews"].get("avg_rating"),
                "review_five_star_rate": regions[key]["insights"]["reviews"].get("five_star_rate"),
                "review_suspicious_rate": regions[key]["insights"]["reviews"].get("suspicious_rate"),
            }
            for key in REGIONS
        ],
    }


def write_outputs(regions: dict[str, dict], summary: dict, shop_indexes: dict[str, dict]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    (PROCESSED_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DOCS_DATA_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for key, payload in regions.items():
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        (PROCESSED_DIR / f"{key}.json").write_text(text, encoding="utf-8")
        (DOCS_DATA_DIR / f"{key}.json").write_text(text, encoding="utf-8")

    for key, index in shop_indexes.items():
        text = json.dumps(index, ensure_ascii=False, indent=2)
        (PROCESSED_DIR / f"shops_{key}.json").write_text(text, encoding="utf-8")
        (DOCS_DATA_DIR / f"shops_{key}.json").write_text(text, encoding="utf-8")


def main() -> None:
    jst = timezone(timedelta(hours=9))
    updated_at = datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")

    regions = {}
    shop_indexes = {}
    for key in REGIONS:
        payload, shop_index = scrape_region(key)
        regions[key] = payload
        shop_indexes[key] = shop_index

    summary = build_summary(regions, updated_at)
    write_outputs(regions, summary, shop_indexes)
    print(f"Done. Updated at {updated_at}")


if __name__ == "__main__":
    main()
