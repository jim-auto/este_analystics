"""Weekly snapshot history and week-over-week deltas."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
HISTORY_DIR = ROOT / "data" / "history"
DOCS_HISTORY = ROOT / "docs" / "data" / "history.json"
MAX_SNAPSHOTS = 12


def _snapshot_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    cross_regions = {r["key"]: r for r in (summary.get("cross") or {}).get("regions", [])}
    bbs_regions = {r["key"]: r for r in (summary.get("bbs") or {}).get("regions", [])}
    review_regions = {r["key"]: r for r in (summary.get("reviews") or {}).get("regions", [])}

    regions = []
    for row in summary.get("regions", []):
        key = row["key"]
        cross = cross_regions.get(key, {})
        bbs = bbs_regions.get(key, {})
        rev = review_regions.get(key, {})
        regions.append(
            {
                "key": key,
                "label": row.get("label"),
                "price_median": row.get("price_median"),
                "price_min": row.get("price_min"),
                "price_max": row.get("price_max"),
                "available_now": row.get("available_now"),
                "sampled_shops": row.get("sampled_shops"),
                "review_avg": row.get("review_avg"),
                "review_five_star_rate": row.get("review_five_star_rate"),
                "review_suspicious_rate": row.get("review_suspicious_rate"),
                "bbs_caution_rate": bbs.get("caution_rate"),
                "bbs_positive_rate": bbs.get("positive_rate"),
                "cross_gap_count": cross.get("gap_count"),
                "cross_matched_shops": cross.get("matched_shops"),
                "parsed_reviews": rev.get("parsed_count"),
            }
        )

    return {
        "updated_at": summary.get("updated_at"),
        "regions": regions,
    }


def save_snapshot(summary: dict[str, Any], date_str: str | None = None) -> Path:
    jst = timezone(timedelta(hours=9))
    date_str = date_str or datetime.now(jst).strftime("%Y-%m-%d")
    day_dir = HISTORY_DIR / date_str
    day_dir.mkdir(parents=True, exist_ok=True)

    metrics = _snapshot_metrics(summary)
    metrics["date"] = date_str
    path = day_dir / "metrics.json"
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_all_snapshots() -> list[dict[str, Any]]:
    if not HISTORY_DIR.exists():
        return []

    snapshots: list[dict[str, Any]] = []
    for day_dir in sorted(HISTORY_DIR.iterdir()):
        if not day_dir.is_dir():
            continue
        metrics_file = day_dir / "metrics.json"
        if not metrics_file.exists():
            continue
        try:
            snapshots.append(json.loads(metrics_file.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue

    snapshots.sort(key=lambda s: s.get("date", ""))
    return snapshots[-MAX_SNAPSHOTS:]


def _delta(current: Any, previous: Any) -> dict[str, Any] | None:
    if current is None or previous is None:
        return None
    try:
        cur = float(current)
        prev = float(previous)
    except (TypeError, ValueError):
        return None
    diff = cur - prev
    return {
        "current": current,
        "previous": previous,
        "delta": round(diff, 2) if isinstance(current, float) else int(diff),
    }


def build_history_payload(summary: dict[str, Any]) -> dict[str, Any]:
    save_snapshot(summary)
    snapshots = _load_all_snapshots()

    changes: dict[str, dict[str, dict[str, Any]]] = {}
    if len(snapshots) >= 2:
        current = snapshots[-1]
        previous = snapshots[-2]
        cur_map = {r["key"]: r for r in current.get("regions", [])}
        prev_map = {r["key"]: r for r in previous.get("regions", [])}

        for key in cur_map:
            if key not in prev_map:
                continue
            c, p = cur_map[key], prev_map[key]
            region_changes = {}
            for field in (
                "price_median",
                "review_avg",
                "review_five_star_rate",
                "review_suspicious_rate",
                "bbs_caution_rate",
                "cross_gap_count",
                "available_now",
            ):
                d = _delta(c.get(field), p.get(field))
                if d is not None:
                    region_changes[field] = d
            if region_changes:
                changes[key] = region_changes

    return {
        "snapshot_count": len(snapshots),
        "latest_date": snapshots[-1]["date"] if snapshots else None,
        "previous_date": snapshots[-2]["date"] if len(snapshots) >= 2 else None,
        "snapshots": snapshots,
        "changes": changes,
        "notes": _history_notes(changes),
    }


def _history_notes(changes: dict[str, dict[str, dict[str, Any]]]) -> list[str]:
    notes: list[str] = []
    for key, region_changes in changes.items():
        price = region_changes.get("price_median")
        if price and abs(price["delta"]) >= 500:
            direction = "上昇" if price["delta"] > 0 else "下降"
            notes.append(
                f"{key}: 90分中央値が ¥{price['previous']:,} → ¥{price['current']:,}（{direction}）"
            )
        gap = region_changes.get("cross_gap_count")
        if gap and gap["delta"] != 0:
            notes.append(f"{key}: クロスギャップ店舗数 {gap['previous']} → {gap['current']}")
    return notes[:6]
