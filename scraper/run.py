"""Main scraper entry point."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scraper.analyze import summarize_coupons, summarize_rankings, summarize_shops
from scraper.config import REGIONS, SHOPLIST_MAX_PAGES
from scraper.fetch import fetch_html
from scraper.parse_couponlist import parse_couponlist
from scraper.parse_ranking import parse_ranking
from scraper.parse_shoplist import parse_shoplist_pages

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DATA_DIR = ROOT / "docs" / "data"


def _shoplist_paths(slug: str) -> list[str]:
    paths = [f"/{slug}/shoplist/"]
    for page in range(2, SHOPLIST_MAX_PAGES + 1):
        paths.append(f"/{slug}/shoplist/p{page}/")
    return paths


def scrape_region(key: str) -> dict:
    cfg = REGIONS[key]
    slug = cfg["slug"]

    print(f"[{cfg['label']}] fetching rankings...")
    rankings = parse_ranking(fetch_html(f"/{slug}/ranking/"))

    print(f"[{cfg['label']}] fetching coupons...")
    coupons = parse_couponlist(fetch_html(f"/{slug}/couponlist/"))

    print(f"[{cfg['label']}] fetching shoplist ({SHOPLIST_MAX_PAGES} pages)...")
    shop_pages = [fetch_html(path) for path in _shoplist_paths(slug)]
    shops, shop_meta = parse_shoplist_pages(shop_pages)

    return {
        "region_key": key,
        "region_label": cfg["label"],
        "region_subtitle": cfg["subtitle"],
        "region_description": cfg["description"],
        "source_urls": {
            "ranking": f"https://estama.jp/{slug}/ranking/",
            "coupons": f"https://estama.jp/{slug}/couponlist/",
            "shoplist": f"https://estama.jp/{slug}/shoplist/",
        },
        "shop_meta": shop_meta,
        "rankings": rankings,
        "coupons": coupons,
        "shops_sample": shops,
        "insights": {
            "shops": summarize_shops(shops),
            "rankings": summarize_rankings(rankings),
            "coupons": summarize_coupons(coupons),
        },
    }


def build_summary(regions: dict[str, dict], updated_at: str) -> dict:
    return {
        "updated_at": updated_at,
        "disclaimer": (
            "本サイトはエステ魂（estama.jp）の公開情報を分析・再整理した非公式サイトです。"
            "予約・最新情報は公式サイトをご確認ください。"
        ),
        "source": "https://estama.jp/",
        "regions": [
            {
                "key": key,
                "label": REGIONS[key]["label"],
                "subtitle": REGIONS[key]["subtitle"],
                "total_shops": regions[key]["shop_meta"].get("total_shops"),
                "sampled_shops": regions[key]["shop_meta"].get("sampled_shops"),
                "coupon_count": len(regions[key]["coupons"]),
                "price_median": regions[key]["insights"]["shops"]["price_90min"]["median"],
                "available_now": regions[key]["insights"]["shops"]["available_now_count"],
            }
            for key in REGIONS
        ],
    }


def write_outputs(regions: dict[str, dict], summary: dict) -> None:
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


def main() -> None:
    jst = timezone(timedelta(hours=9))
    updated_at = datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")

    regions = {}
    for key in REGIONS:
        regions[key] = scrape_region(key)

    summary = build_summary(regions, updated_at)
    write_outputs(regions, summary)
    print(f"Done. Updated at {updated_at}")


if __name__ == "__main__":
    main()
