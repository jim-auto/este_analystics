"""Statistical helpers for review analysis (stdlib only)."""

from __future__ import annotations

import math
from statistics import mean, median, quantiles, stdev
from typing import Any


def _safe_stdev(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    return stdev(values)


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    qs = quantiles(values, n=100, method="inclusive")
    idx = max(0, min(99, int(round(p * 100)) - 1))
    return round(qs[idx], 2)


def pearson_correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return round(num / (den_x * den_y), 3)


def wilson_ci(successes: int, n: int, z: float = 1.96) -> dict[str, float] | None:
    if n <= 0:
        return None
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return {
        "point": round(p * 100, 1),
        "low": round(max(0.0, center - margin) * 100, 1),
        "high": round(min(1.0, center + margin) * 100, 1),
    }


def binomial_z_test(successes: int, n: int, p0: float) -> dict[str, Any] | None:
    """Two-sided normal approximation for proportion vs null p0."""
    if n <= 0 or p0 <= 0 or p0 >= 1:
        return None
    p_hat = successes / n
    se = math.sqrt(p0 * (1 - p0) / n)
    if se == 0:
        return None
    z = (p_hat - p0) / se
    significant = abs(z) >= 1.96
    return {
        "null_hypothesis_pct": round(p0 * 100, 1),
        "observed_pct": round(p_hat * 100, 1),
        "z_score": round(z, 2),
        "significant_at_005": significant,
    }


def chi_square_2x2(a: int, b: int, c: int, d: int) -> dict[str, Any] | None:
    """Test independence in 2x2 table [[a,b],[c,d]]."""
    n = a + b + c + d
    if n == 0:
        return None
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    expected = [
        row1 * col1 / n,
        row1 * col2 / n,
        row2 * col1 / n,
        row2 * col2 / n,
    ]
    observed = [a, b, c, d]
    chi2 = sum(
        (o - e) ** 2 / e for o, e in zip(observed, expected) if e > 0
    )
    significant = chi2 >= 3.841
    return {
        "chi2": round(chi2, 2),
        "df": 1,
        "significant_at_005": significant,
    }


def skewness(values: list[float]) -> float | None:
    n = len(values)
    if n < 3:
        return None
    m = mean(values)
    s = stdev(values)
    if s == 0:
        return 0.0
    return round(sum(((x - m) / s) ** 3 for x in values) / n, 3)


def shannon_entropy(counts: list[int]) -> float | None:
    total = sum(counts)
    if total == 0:
        return None
    ent = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            ent -= p * math.log2(p)
    return round(ent, 3)


def group_mean(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "std": None}
    return {
        "count": len(values),
        "mean": round(mean(values), 2),
        "median": round(median(values), 2),
        "std": round(_safe_stdev(values), 2) if len(values) >= 2 else None,
    }


def price_tertile_stats(
    reviews: list[dict[str, Any]],
) -> dict[str, Any] | None:
    pairs = [(r["price_90min"], r["rating"]) for r in reviews if r.get("price_90min") and r.get("rating")]
    if len(pairs) < 9:
        return None

    pairs.sort(key=lambda x: x[0])
    third = len(pairs) // 3
    tiers = {
        "low": pairs[:third],
        "mid": pairs[third : 2 * third],
        "high": pairs[2 * third :],
    }
    result = {}
    for name, group in tiers.items():
        prices = [p for p, _ in group]
        ratings = [r for _, r in group]
        result[name] = {
            "count": len(group),
            "price_range": [min(prices), max(prices)],
            "mean_rating": round(mean(ratings), 2),
            "five_star_rate": round(sum(1 for r in ratings if r >= 5.0) / len(ratings) * 100, 1),
        }
    return result


def interpret_correlation(r: float | None) -> str | None:
    if r is None:
        return None
    ar = abs(r)
    if ar < 0.1:
        strength = "ほぼ無相関"
    elif ar < 0.3:
        strength = "弱い相関"
    elif ar < 0.5:
        strength = "中程度の相関"
    else:
        strength = "比較的強い相関"
    direction = "正" if r > 0 else "負"
    return f"{strength}（{direction}）"
