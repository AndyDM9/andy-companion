"""How sure a measured number is (PLAN B33, B34): Wilson 95% intervals for counts and nearest-rank
percentiles for times. Used by the evaluations and the charts, so every figure can carry its uncertainty."""

from __future__ import annotations

import math
from typing import Iterable, Optional, Tuple

Z95 = 1.959964


def wilson(k: float, n: int, z: float = Z95) -> Tuple[float, float]:
    """The 95% interval for k successes in n tries, as fractions (0..1). Sound at 0 of n and n of n, where
    the plain k/n ± margin is not. k may be a mean of runs (the scam check's 55.7); n must be positive."""
    if n <= 0:
        raise ValueError("n must be positive")
    k = min(max(float(k), 0.0), float(n))
    p = k / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    d = 1 + z * z / n
    return max(0.0, (centre - margin) / d), min(1.0, (centre + margin) / d)


def percent_range(k: float, n: int) -> str:
    """'88.6–99.1%': the interval as people read it."""
    lo, hi = wilson(k, n)
    return f"{lo * 100:.1f}–{hi * 100:.1f}%"


def percentile(values: Iterable[float], q: float) -> Optional[float]:
    """The nearest-rank q-th percentile (0 < q <= 100) of the values, or None when there are none."""
    xs = sorted(values)
    if not xs:
        return None
    rank = max(1, math.ceil(q / 100 * len(xs)))
    return xs[min(rank, len(xs)) - 1]
