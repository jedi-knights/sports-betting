"""Calibration quality metrics: Brier score, log-loss, and ECE."""

from __future__ import annotations

import math
from collections import defaultdict


def brier_score(probs: list[float], outcomes: list[int]) -> float:
    """Mean squared error between predicted probabilities and binary outcomes.

    Range is [0, 1]; 0 is perfect, 0.25 corresponds to random 50/50 guessing.

    Args:
        probs: Predicted probabilities in [0, 1].
        outcomes: Binary labels — 1 if the outcome occurred, 0 otherwise.

    Returns:
        Brier score in [0, 1].

    Raises:
        ValueError: If probs is empty or lengths differ.
    """
    _validate(probs, outcomes)
    n = len(probs)
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / n


def log_loss(probs: list[float], outcomes: list[int]) -> float:
    """Negative log-likelihood (cross-entropy) between predictions and outcomes.

    Heavily penalises confident wrong predictions. Lower is better.

    Args:
        probs: Predicted probabilities in [0, 1].
        outcomes: Binary labels — 1 if the outcome occurred, 0 otherwise.

    Returns:
        Log-loss ≥ 0.

    Raises:
        ValueError: If probs is empty or lengths differ.
    """
    _validate(probs, outcomes)
    eps = 1e-15
    n = len(probs)
    total = sum(
        o * math.log(max(p, eps)) + (1 - o) * math.log(max(1 - p, eps))
        for p, o in zip(probs, outcomes)
    )
    return -total / n


def expected_calibration_error(
    probs: list[float],
    outcomes: list[int],
    n_bins: int = 10,
) -> float:
    """Weighted average deviation between predicted probability and observed frequency.

    Divides [0, 1] into n_bins equal-width buckets, computes the deviation
    between mean predicted probability and observed win rate per bucket, and
    returns the sample-weighted average across all non-empty buckets.

    Args:
        probs: Predicted probabilities in [0, 1].
        outcomes: Binary labels — 1 if the outcome occurred, 0 otherwise.
        n_bins: Number of equal-width calibration bins. Defaults to 10.

    Returns:
        ECE in [0, 1]; 0 is perfect calibration.

    Raises:
        ValueError: If probs is empty or lengths differ.
    """
    _validate(probs, outcomes)
    n = len(probs)
    bins: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for p, o in zip(probs, outcomes):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, o))

    total_error = 0.0
    for bucket in bins.values():
        mean_pred = sum(p for p, _ in bucket) / len(bucket)
        mean_outcome = sum(o for _, o in bucket) / len(bucket)
        total_error += (len(bucket) / n) * abs(mean_pred - mean_outcome)

    return total_error


def _validate(probs: list[float], outcomes: list[int]) -> None:
    if not probs:
        raise ValueError("probs must not be empty")
    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must have the same length")
