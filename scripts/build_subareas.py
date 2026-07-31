"""Rebuild subarea indexes from existing region + shops JSON (no network)."""
import json
from pathlib import Path

from scraper.config import REGIONS
from scraper.subarea_index import build_subarea_index

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "data"
PROCESSED = ROOT / "data" / "processed"


def main() -> None:
    for key in REGIONS:
        region_path = DOCS / f"{key}.json"
        shops_path = DOCS / f"shops_{key}.json"
        if not region_path.exists() or not shops_path.exists():
            print(key, "skip - missing files")
            continue

        region = json.loads(region_path.read_text(encoding="utf-8"))
        shop_index = json.loads(shops_path.read_text(encoding="utf-8"))

        # Reconstruct minimal shop rows from shop_index + price_by_sub_area shop counts
        # Full shop list isn't in JSON; use shop_index entries grouped by sub_area
        # plus expand with price_by_sub_area only areas (stats from insights)
        shops_from_index = [
            {
                "id": s["id"],
                "name": s["name"],
                "sub_area": s.get("sub_area"),
                "price_90min": s.get("price_90min"),
                "available_now": s.get("available_now"),
                "coupon_count": s.get("coupon_count"),
            }
            for s in shop_index.get("shops", [])
        ]

        # For areas in price_by_sub_area not covered, add placeholder shops from insights count
        # Subarea index needs >=2 shops per area - indexed shops only is partial but usable
        subarea = build_subarea_index(
            key,
            region.get("region_label", REGIONS[key]["label"]),
            shops_from_index,
            shop_index,
        )

        # Merge price stats from insights for areas missing from index-only build
        insight_areas = {
            r["name"]: r
            for r in region.get("insights", {}).get("shops", {}).get("price_by_sub_area", [])
        }
        existing = {a["name"]: a for a in subarea["areas"]}
        for name, row in insight_areas.items():
            if name in existing:
                continue
            if row.get("shop_count", 0) < 2:
                continue
            subarea["areas"].append(
                {
                    "name": name,
                    "shop_count": row.get("shop_count"),
                    "priced_count": row.get("priced_shop_count"),
                    "price_median": row.get("price_median"),
                    "price_min": row.get("price_min"),
                    "price_max": row.get("price_max"),
                    "available_now": 0,
                    "with_coupon": 0,
                    "signal_shop_count": 0,
                    "signal_shops": [],
                    "budget_shops": [],
                    "shops": [],
                }
            )
        subarea["areas"].sort(key=lambda a: (-(a.get("shop_count") or 0), a["name"]))
        subarea["area_count"] = len(subarea["areas"])

        text = json.dumps(subarea, ensure_ascii=False, indent=2)
        (DOCS / f"subareas_{key}.json").write_text(text, encoding="utf-8")
        (PROCESSED / f"subareas_{key}.json").write_text(text, encoding="utf-8")
        print(key, subarea["area_count"], "areas")


if __name__ == "__main__":
    main()
