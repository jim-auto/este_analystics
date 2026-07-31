"""Weekly digest: new gaps, movers, BBS keyword shifts."""

from __future__ import annotations

from typing import Any


def _gap_shop_set(snapshot: dict[str, Any]) -> set[str]:
    return {f"{s.get('region_key')}:{s.get('id')}" for s in snapshot.get("cross_gap_shops", [])}


def _keyword_map(snapshot: dict[str, Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in snapshot.get("bbs_keywords", []):
        result[row["key"]] = row.get("keywords") or {}
    return result


def build_weekly_digest(summary: dict[str, Any], history: dict[str, Any]) -> dict[str, Any]:
    snapshots = history.get("snapshots") or []
    cross = summary.get("cross") or {}
    bbs = summary.get("bbs") or {}
    highlights = summary.get("highlights") or {}

    new_gap_shops: list[dict[str, Any]] = []
    bbs_spikes: list[dict[str, Any]] = []

    if len(snapshots) >= 2:
        prev, curr = snapshots[-2], snapshots[-1]
        prev_gaps = _gap_shop_set(prev)
        for shop in curr.get("cross_gap_shops", []):
            key = f"{shop.get('region_key')}:{shop.get('id')}"
            if key not in prev_gaps:
                new_gap_shops.append(shop)

        prev_kw = _keyword_map(prev)
        curr_kw = _keyword_map(curr)
        for region_key, keywords in curr_kw.items():
            for word, count in keywords.items():
                prev_count = (prev_kw.get(region_key) or {}).get(word, 0)
                if count >= 3 and count - prev_count >= 2:
                    label = next(
                        (r["label"] for r in bbs.get("regions", []) if r["key"] == region_key),
                        region_key,
                    )
                    bbs_spikes.append(
                        {
                            "region_key": region_key,
                            "region_label": label,
                            "keyword": word,
                            "count": count,
                            "delta": count - prev_count,
                        }
                    )
        bbs_spikes.sort(key=lambda x: x["delta"], reverse=True)

    # First run: treat current top gaps as "watch list"
    if not new_gap_shops and cross.get("top_gaps"):
        new_gap_shops = cross.get("top_gaps", [])[:6]

    return {
        "new_gap_shops": new_gap_shops[:8],
        "ranking_movers": (highlights.get("ranking_movers") or [])[:6],
        "best_coupons": (highlights.get("best_coupons") or [])[:4],
        "bbs_keyword_spikes": bbs_spikes[:6],
        "has_prior_snapshot": len(snapshots) >= 2,
    }
