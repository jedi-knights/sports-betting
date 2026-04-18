"""Reliability diagram (calibration curve) data generation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class CalibrationCurve:
    """Data for plotting a reliability diagram.

    Each list has one entry per non-empty bin; empty bins are omitted.
    Plot bin_centers on the X-axis and observed_frequencies on the Y-axis.
    A perfectly calibrated model lies on the diagonal (center == frequency).

    Attributes:
        bin_centers: Mean predicted probability within each non-empty bin.
        observed_frequencies: Fraction of positive outcomes in each bin.
        bin_counts: Number of predictions that fell into each bin.
    """

    bin_centers: list[float] = field(default_factory=list)
    observed_frequencies: list[float] = field(default_factory=list)
    bin_counts: list[int] = field(default_factory=list)


def calibration_curve(
    probs: list[float],
    outcomes: list[int],
    n_bins: int = 10,
) -> CalibrationCurve:
    """Compute reliability diagram data by binning predictions.

    Args:
        probs: Predicted probabilities in [0, 1].
        outcomes: Binary labels — 1 if the outcome occurred, 0 otherwise.
        n_bins: Number of equal-width bins spanning [0, 1]. Defaults to 10.

    Returns:
        A CalibrationCurve with one entry per non-empty bin, sorted by
        ascending bin center.

    Raises:
        ValueError: If probs is empty or lengths differ.
    """
    if not probs:
        raise ValueError("probs must not be empty")
    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must have the same length")

    bins: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for p, o in zip(probs, outcomes):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, o))

    centers: list[float] = []
    frequencies: list[float] = []
    counts: list[int] = []

    for idx in sorted(bins.keys()):
        bucket = bins[idx]
        centers.append(sum(p for p, _ in bucket) / len(bucket))
        frequencies.append(sum(o for _, o in bucket) / len(bucket))
        counts.append(len(bucket))

    return CalibrationCurve(
        bin_centers=centers,
        observed_frequencies=frequencies,
        bin_counts=counts,
    )
