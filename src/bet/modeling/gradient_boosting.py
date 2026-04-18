"""Gradient boosting classification model for game outcome prediction.

Wraps scikit-learn's GradientBoostingClassifier. Handles both binary outcomes
(home/away, e.g. NFL) and three-way outcomes (home/draw/away, e.g. soccer)
transparently based on what labels appear in training data.

Gradient boosting is generally the highest-accuracy approach on sports tabular
data, but tree-based models produce poorly calibrated probabilities — they tend
to cluster predictions near the centre of the probability range. Always wrap
this model with a ``CalibratedModel`` before using probabilities for value
analysis. See ``docs/modeling/models/ml-methods.md``.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.exceptions import NotFittedError

from .types import FeatureSet, ProbabilityEstimate, TrainingExample


def _outcome_label(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home_win"
    if home_score < away_score:
        return "away_win"
    return "draw"


class GradientBoostingModel:
    """Gradient-boosted decision tree classifier for game outcome prediction.

    Works with any feature set; feature keys are determined from the first
    training example and must be consistent across all examples and at
    predict time.

    Does not require feature scaling (tree-based models are scale-invariant).

    Args:
        n_estimators: Number of boosting stages (trees). More estimators
            improve accuracy but increase training time.
        max_depth: Maximum depth of each individual tree. Shallow trees
            (3–5) generalise better on sports data.
        learning_rate: Shrinkage factor applied to each tree's contribution.
            Lower values require more trees but reduce overfitting.
        subsample: Fraction of training data sampled per tree. Values below
            1.0 introduce stochastic gradient boosting, which reduces
            variance.
    """

    model_id = "gradient_boosting"

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 4,
        learning_rate: float = 0.1,
        subsample: float = 0.8,
    ) -> None:
        self._model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
        )
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
        y = [_outcome_label(ex.outcome.home_score, ex.outcome.away_score) for ex in examples]

        self._model.fit(x, y)
        self._fitted = True

    def predict(self, features: FeatureSet) -> ProbabilityEstimate:
        """Predict win probabilities using the fitted gradient boosting model.

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
        proba = self._model.predict_proba(x)[0]
        prob_map = dict(zip(self._model.classes_, proba, strict=False))

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
