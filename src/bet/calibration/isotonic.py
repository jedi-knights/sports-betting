"""Isotonic regression calibrator."""

from __future__ import annotations

import numpy as np
from sklearn.exceptions import NotFittedError
from sklearn.isotonic import IsotonicRegression as _IsotonicRegression


class IsotonicCalibrator:
    """Isotonic regression calibrator: fits a monotone non-decreasing step function.

    More flexible than Platt scaling but requires more calibration data to
    avoid overfitting. Best suited for tree-based models (XGBoost, LightGBM,
    Random Forests).

    Fit on a held-out calibration set, not on training data.
    """

    def __init__(self) -> None:
        self._model = _IsotonicRegression(out_of_bounds="clip")
        self._fitted = False

    def fit(self, probs: list[float], outcomes: list[int]) -> None:
        """Fit isotonic regression on raw probabilities vs. binary outcomes.

        Args:
            probs: Raw model-predicted home_win probabilities.
            outcomes: Binary labels — 1 if home won, 0 otherwise.

        Raises:
            ValueError: If probs is empty or lengths differ.
        """
        if not probs:
            raise ValueError("fit requires at least one example")
        if len(probs) != len(outcomes):
            raise ValueError("probs and outcomes must have the same length")
        x = np.array(probs, dtype=float)
        y = np.array(outcomes, dtype=float)
        self._model.fit(x, y)
        self._fitted = True

    def transform(self, probs: list[float]) -> list[float]:
        """Apply isotonic regression to raw probabilities.

        Args:
            probs: Raw model-predicted probabilities.

        Returns:
            Calibrated probabilities in [0, 1]; same length as input.

        Raises:
            NotFittedError: If called before fit.
        """
        if not self._fitted:
            raise NotFittedError("call fit() before transform()")
        x = np.array(probs, dtype=float)
        return list(self._model.predict(x))
