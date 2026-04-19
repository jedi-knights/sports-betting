"""Bivariate Poisson model for soccer goal prediction.

Goal counts for home and away teams are modelled as independent Poisson
random variables:

    λ_home = home_baseline × home_attack × away_defense
    λ_away = away_baseline × away_attack × home_defense

where ``home_attack`` and ``away_defense`` are normalized strength features
(average = 1.0) from ``SoccerFeatureExtractor``.

The Dixon-Coles correction adjusts probabilities for low-scoring scorelines
(0-0, 1-0, 0-1, 1-1) using a small negative ``rho`` parameter. This
corrects the slight overestimation of draws that pure Poisson produces.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import poisson

from .types import FeatureSet, ProbabilityEstimate, TrainingExample


class PoissonModel:
    """Bivariate Poisson model with optional Dixon-Coles correction.

    ``fit`` estimates home and away scoring baselines from training outcomes.
    ``predict`` uses pre-extracted attack/defense strength features.

    Args:
        rho: Dixon-Coles correlation parameter. Negative values (typically
            -0.1 to -0.2) reduce draw probability for low-scoring games.
            Set to 0.0 to disable the correction.
        max_goals: Maximum number of goals to consider per team when building
            the score probability matrix. 10 captures > 99.9% of real games.
    """

    model_id = "poisson"

    def __init__(self, rho: float = -0.13, max_goals: int = 10) -> None:
        if rho > 0:
            raise ValueError(f"rho must be <= 0; got {rho}")
        self._rho = rho
        self._max_goals = max_goals
        self._home_baseline = 1.5
        self._away_baseline = 1.1

    def fit(self, examples: list[TrainingExample]) -> None:
        """Estimate home and away scoring baselines from historical outcomes.

        The baselines represent average goals per game for each side, used
        to scale normalized attack/defense features in ``predict``.

        Args:
            examples: Historical games; only ``outcome.home_score`` and
                ``outcome.away_score`` are used.
        """
        if not examples:
            return
        home_goals = [ex.outcome.home_score for ex in examples]
        away_goals = [ex.outcome.away_score for ex in examples]
        self._home_baseline = sum(home_goals) / len(home_goals)
        self._away_baseline = sum(away_goals) / len(away_goals)

    def predict(self, features: FeatureSet) -> ProbabilityEstimate:
        """Predict home/draw/away probabilities via the Poisson score matrix.

        Expected goals are computed as:

            λ_home = home_baseline × features["home_attack"] × features["away_defense"]
            λ_away = away_baseline × features["away_attack"] × features["home_defense"]

        Args:
            features: Feature set from ``SoccerFeatureExtractor``.

        Returns:
            A ProbabilityEstimate with ``draw`` populated (soccer has draws).
        """
        home_attack = features.features.get("home_attack", 1.0)
        home_defense = features.features.get("home_defense", 1.0)
        away_attack = features.features.get("away_attack", 1.0)
        away_defense = features.features.get("away_defense", 1.0)

        lambda_home = self._home_baseline * home_attack * away_defense
        lambda_away = self._away_baseline * away_attack * home_defense

        matrix = self._score_matrix(lambda_home, lambda_away)
        total = matrix.sum()
        if total <= 0:
            raise ValueError(f"score matrix sum is non-positive ({total}); verify lambda values")

        home_win = float(np.sum(np.tril(matrix, -1))) / total
        away_win = float(np.sum(np.triu(matrix, 1))) / total
        draw = float(np.trace(matrix)) / total

        return ProbabilityEstimate(
            event_id=features.event_id,
            model_id=self.model_id,
            generated_at=features.as_of,
            home_win=home_win,
            away_win=away_win,
            draw=draw,
        )

    def _score_matrix(self, lambda_home: float, lambda_away: float) -> np.ndarray:
        """Build the joint probability matrix P(home_goals=i, away_goals=j).

        Row index is home goals; column index is away goals. Dixon-Coles
        correction is applied to the four low-scoring cells.

        Args:
            lambda_home: Expected home goals.
            lambda_away: Expected away goals.

        Returns:
            A (max_goals+1) × (max_goals+1) array of joint probabilities.
        """
        goals = np.arange(self._max_goals + 1)
        home_probs = poisson.pmf(goals, lambda_home)
        away_probs = poisson.pmf(goals, lambda_away)
        matrix = np.outer(home_probs, away_probs)

        if self._rho != 0.0:
            matrix[0, 0] *= 1.0 - lambda_home * lambda_away * self._rho
            matrix[1, 0] *= 1.0 + lambda_away * self._rho
            matrix[0, 1] *= 1.0 + lambda_home * self._rho
            matrix[1, 1] *= 1.0 - self._rho

        matrix = np.clip(matrix, 0.0, None)
        return matrix
