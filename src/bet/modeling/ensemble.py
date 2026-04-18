"""Ensemble model that averages predictions from multiple component models.

Combines any number of models that implement the ``Model`` protocol by
averaging their raw probability outputs. Averaging reduces variance by
cancelling out individual model errors — the gain is largest when component
models make different types of errors (e.g., a linear logistic regression
paired with a non-linear gradient boosting model).

See ``docs/modeling/models/ml-methods.md`` for a discussion of when ensembles
add value over individual models.
"""

from __future__ import annotations

from .protocols import Model
from .types import FeatureSet, ProbabilityEstimate, TrainingExample


class EnsembleModel:
    """Averages win probability predictions from multiple component models.

    All component models must implement ``fit(examples)`` and
    ``predict(features)``. Each model is fit independently on the same
    training examples. At prediction time, probabilities are averaged and
    re-normalised to sum to exactly 1.0.

    Args:
        models: Component models to average. Must share a compatible feature
            interface — all models see the same FeatureSet at predict time.

    Raises:
        ValueError: If ``models`` is empty at predict time.
    """

    model_id = "ensemble"

    def __init__(self, models: list[Model]) -> None:
        self._models = models

    def fit(self, examples: list[TrainingExample]) -> None:
        """Fit every component model on the same training examples.

        Args:
            examples: Labelled games passed unchanged to each component model.
        """
        for model in self._models:
            model.fit(examples)

    def predict(self, features: FeatureSet) -> ProbabilityEstimate:
        """Average win probabilities across all component models.

        Probabilities from each model are summed and divided by the number
        of models, then re-normalised to guarantee they sum to exactly 1.0.
        Draw probability is included in the average only when at least one
        component model produces a non-None draw estimate.

        Args:
            features: Feature set passed unchanged to each component model.

        Returns:
            ProbabilityEstimate whose probabilities are the normalised average
            of all component model outputs.

        Raises:
            ValueError: If no component models are registered.
        """
        if not self._models:
            raise ValueError("EnsembleModel requires at least one model")

        estimates = [m.predict(features) for m in self._models]

        avg_home = sum(e.home_win for e in estimates) / len(estimates)
        avg_away = sum(e.away_win for e in estimates) / len(estimates)

        draw_estimates = [e.draw for e in estimates if e.draw is not None]
        avg_draw: float | None = (
            sum(draw_estimates) / len(draw_estimates) if draw_estimates else None
        )

        total = avg_home + avg_away + (avg_draw or 0.0)
        if total > 0:
            avg_home /= total
            avg_away /= total
            if avg_draw is not None:
                avg_draw /= total

        return ProbabilityEstimate(
            event_id=features.event_id,
            model_id=self.model_id,
            generated_at=features.as_of,
            home_win=avg_home,
            away_win=avg_away,
            draw=avg_draw,
        )
