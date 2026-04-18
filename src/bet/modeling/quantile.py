"""Quantile regression model for spread/totals markets.

Predicts the distribution of home team point margin (home_score -
away_score) using multiple quantile regressors. Win probability is derived
from the predicted margin distribution using a normal approximation.

This approach is complementary to direct classification (EloModel,
LogisticRegressionModel) because it targets the tails of the outcome
distribution rather than the most likely category. Point spreads explain
approximately 86% of the variance in NFL outcomes — quantile regression
directly targets that distribution.

See ``docs/modeling/models/quantile-regression.md`` for the theory and
``docs/modeling/models/ml-methods.md`` for comparison with other methods.
"""

from __future__ import annotations

import numpy as np
from scipy import stats
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import QuantileRegressor

from .types import FeatureSet, ProbabilityEstimate, TrainingExample

# Quantile levels to fit; median (0.5) is used for the win probability conversion.
_QUANTILE_LEVELS = (0.1, 0.25, 0.5, 0.75, 0.9)


class QuantileRegressionModel:
    """Quantile regression model that predicts win probability from margin distribution.

    Fits one ``QuantileRegressor`` per quantile level on the home team's
    point margin (home_score - away_score). Win probability is computed as:

        P(home_win) = Φ(predicted_median / margin_std)

    where Φ is the standard normal CDF, ``predicted_median`` is the τ=0.5
    prediction, and ``margin_std`` is the standard deviation of training
    margins. This assumes margins are approximately normally distributed
    around the predicted median — a reasonable approximation for most sports.

    For totals and spread markets, use ``predict_quantiles`` to get the full
    margin distribution rather than just the win probability.

    Args:
        alpha: L1 regularisation strength for the quantile regressors.
            0.0 means no regularisation (appropriate for small feature sets).
    """

    model_id = "quantile_regression"

    def __init__(self, alpha: float = 0.0) -> None:
        self._alpha = alpha
        self._quantile_models: dict[float, QuantileRegressor] = {}
        self._feature_keys: list[str] = []
        self._margin_std: float = 1.0
        self._fitted = False

    def fit(self, examples: list[TrainingExample]) -> None:
        """Fit one quantile regressor per quantile level on home point margin.

        The target variable is ``home_score - away_score``. Feature keys are
        sorted alphabetically from the first example and held fixed.

        Args:
            examples: Labelled games; must share the same feature keys.

        Raises:
            ValueError: If ``examples`` is empty.
        """
        if not examples:
            raise ValueError("fit requires at least one training example")

        self._feature_keys = sorted(examples[0].feature_set.features.keys())

        x = np.array([[ex.feature_set.features[k] for k in self._feature_keys] for ex in examples])
        y = np.array(
            [ex.outcome.home_score - ex.outcome.away_score for ex in examples],
            dtype=float,
        )

        for q in _QUANTILE_LEVELS:
            model = QuantileRegressor(quantile=q, alpha=self._alpha, solver="highs")
            model.fit(x, y)
            self._quantile_models[q] = model

        self._margin_std = float(np.std(y)) if len(y) > 1 else 1.0
        self._fitted = True

    def predict(self, features: FeatureSet) -> ProbabilityEstimate:
        """Predict win probability using the normal approximation on margin.

        Args:
            features: Feature set with the same keys used during ``fit``.

        Returns:
            ProbabilityEstimate with ``draw=None``; win probability is derived
            from the predicted median margin and training margin spread.

        Raises:
            NotFittedError: If called before ``fit``.
        """
        if not self._fitted:
            raise NotFittedError("call fit() before predict()")

        x = np.array([[features.features[k] for k in self._feature_keys]])
        predicted_median = float(self._quantile_models[0.5].predict(x)[0])

        # P(home_win) = P(margin > 0) ≈ Φ(μ / σ)
        # where μ = predicted median and σ = training margin std dev.
        std = max(self._margin_std, 1.0)
        home_win = float(stats.norm.cdf(predicted_median / std))
        home_win = max(1e-6, min(1.0 - 1e-6, home_win))

        return ProbabilityEstimate(
            event_id=features.event_id,
            model_id=self.model_id,
            generated_at=features.as_of,
            home_win=home_win,
            away_win=1.0 - home_win,
            draw=None,
        )

    def predict_quantiles(self, features: FeatureSet) -> dict[float, float]:
        """Return the predicted margin at each fitted quantile level.

        Useful for pricing spread and totals markets directly without the
        normal approximation. The returned values can be used to estimate
        P(margin > spread_line) by interpolating the quantile function.

        Args:
            features: Feature set with the same keys used during ``fit``.

        Returns:
            Dict mapping each quantile level to its predicted margin value.

        Raises:
            NotFittedError: If called before ``fit``.
        """
        if not self._fitted:
            raise NotFittedError("call fit() before predict()")

        x = np.array([[features.features[k] for k in self._feature_keys]])
        return {q: float(model.predict(x)[0]) for q, model in self._quantile_models.items()}
