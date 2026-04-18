"""Logistic regression model for game outcome prediction.

Wraps scikit-learn's LogisticRegression with L2 regularisation. Handles both
binary outcomes (home/away, e.g. NFL) and three-way outcomes (home/draw/away,
e.g. soccer) transparently based on what labels appear in training data.

Feature ordering is inferred from the first training example and held fixed
across all subsequent predictions.
"""

from __future__ import annotations

import numpy as np
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .types import FeatureSet, ProbabilityEstimate, TrainingExample


def _outcome_label(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home_win"
    if home_score < away_score:
        return "away_win"
    return "draw"


class LogisticRegressionModel:
    """L2-regularised logistic regression for game outcome prediction.

    Works with any feature set; feature keys are determined from the first
    training example and must be consistent across all examples and at
    predict time.

    Args:
        c: Inverse regularisation strength. Smaller c = stronger L2 penalty
            and lower variance. 1.0 is the sklearn default.
    """

    model_id = "logistic_regression"

    def __init__(self, c: float = 1.0) -> None:
        self._c = c
        self._model = LogisticRegression(C=c, solver="lbfgs", max_iter=5000)
        self._scaler = StandardScaler()
        self._feature_keys: list[str] = []
        self._fitted = False

    def fit(self, examples: list[TrainingExample]) -> None:
        """Fit the model on labelled training examples.

        Feature keys are sorted alphabetically from the first example's
        feature dict and used for all subsequent calls.

        Args:
            examples: Labelled games; must share the same feature keys.

        Raises:
            ValueError: If ``examples`` is empty.
        """
        if not examples:
            raise ValueError("fit requires at least one training example")

        self._feature_keys = sorted(examples[0].feature_set.features.keys())

        def _row(ex: TrainingExample) -> list[float]:
            return [ex.feature_set.features[k] for k in self._feature_keys]

        x = np.array([_row(ex) for ex in examples])
        y = [
            _outcome_label(ex.outcome.home_score, ex.outcome.away_score)
            for ex in examples
        ]

        x_scaled = self._scaler.fit_transform(x)
        self._model.fit(x_scaled, y)
        self._fitted = True

    def predict(self, features: FeatureSet) -> ProbabilityEstimate:
        """Predict win probabilities using the fitted logistic regression.

        Args:
            features: Feature set with the same keys used during ``fit``.

        Returns:
            A ProbabilityEstimate where ``draw`` is ``None`` for binary sports.

        Raises:
            NotFittedError: If called before ``fit``.
        """
        if not self._fitted:
            raise NotFittedError("call fit() before predict()")

        x = np.array([[features.features[k] for k in self._feature_keys]])
        x_scaled = self._scaler.transform(x)
        proba = self._model.predict_proba(x_scaled)[0]
        prob_map = dict(zip(self._model.classes_, proba))

        home_win = float(prob_map.get("home_win", 0.0))
        away_win = float(prob_map.get("away_win", 0.0))
        draw_val = prob_map.get("draw")
        draw = float(draw_val) if draw_val is not None else None

        return ProbabilityEstimate(
            event_id=features.event_id,
            model_id=self.model_id,
            generated_at=features.as_of,
            home_win=home_win,
            away_win=away_win,
            draw=draw,
        )
