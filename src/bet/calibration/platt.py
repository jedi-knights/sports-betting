"""Platt scaling calibrator."""

from __future__ import annotations

import numpy as np
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import LogisticRegression


class PlattScaler:
    """Platt scaling: fits logistic regression on top of raw model probabilities.

    Works well when miscalibration is approximately sigmoidal (common in SVMs
    and neural networks). Uses high C (weak regularisation) to approximate the
    original Platt method closely.

    Fit on a held-out calibration set, not on training data, to avoid
    in-sample overfitting.
    """

    def __init__(self) -> None:
        self._model = LogisticRegression(C=1e10, solver="lbfgs")
        self._fitted = False

    def fit(self, probs: list[float], outcomes: list[int]) -> None:
        """Fit logistic regression on raw probabilities vs. binary outcomes.

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
        x = np.array(probs, dtype=float).reshape(-1, 1)
        self._model.fit(x, outcomes)
        self._fitted = True

    def transform(self, probs: list[float]) -> list[float]:
        """Apply Platt scaling to raw probabilities.

        Args:
            probs: Raw model-predicted probabilities.

        Returns:
            Calibrated probabilities in [0, 1]; same length as input.

        Raises:
            NotFittedError: If called before fit.
        """
        if not self._fitted:
            raise NotFittedError("call fit() before transform()")
        x = np.array(probs, dtype=float).reshape(-1, 1)
        return list(self._model.predict_proba(x)[:, 1])
