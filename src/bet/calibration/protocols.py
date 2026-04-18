"""Protocols for the Calibration context."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Calibrator(Protocol):
    """Post-hoc probability calibrator.

    Implementations fit a correction function from raw model scores to
    empirical frequencies, then apply it to new predictions. Always fit
    the calibrator on a held-out validation set, never on training data.
    """

    def fit(self, probs: list[float], outcomes: list[int]) -> None:
        """Learn the calibration mapping from predictions to frequencies.

        Args:
            probs: Raw model-predicted probabilities in [0, 1].
            outcomes: Binary labels — 1 if the outcome occurred, 0 otherwise.
        """
        ...

    def transform(self, probs: list[float]) -> list[float]:
        """Apply the fitted calibration correction.

        Args:
            probs: Raw model-predicted probabilities in [0, 1].

        Returns:
            Calibrated probabilities in [0, 1]; same length as input.
        """
        ...
