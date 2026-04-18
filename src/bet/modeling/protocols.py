"""Protocols (structural interfaces) for the Statistical Modeling context.

Using ``typing.Protocol`` means any class with the right method signatures
satisfies the interface without explicit inheritance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from .types import FeatureSet, ProbabilityEstimate, TrainingExample


@runtime_checkable
class Model(Protocol):
    """Predictive model: fits on historical data, returns probability estimates."""

    @property
    def model_id(self) -> str: ...

    def fit(self, examples: list[TrainingExample]) -> None:
        """Train or update the model using a list of labelled historical games.

        Args:
            examples: Labelled training examples in any order; implementations
                sort by time internally when order matters.
        """
        ...

    def predict(self, features: FeatureSet) -> ProbabilityEstimate:
        """Return win probabilities for one game given its feature set.

        Args:
            features: Pre-computed feature set from a FeatureExtractor.

        Returns:
            A ProbabilityEstimate whose probabilities sum to 1.0.
        """
        ...


@runtime_checkable
class FeatureExtractor(Protocol):
    """Computes a feature set for one game as of a given timestamp.

    Implementations are sport-specific and must enforce the lookahead bias guard:
    no feature may be derived from data recorded after ``as_of``.
    """

    def fit(self, examples: list[TrainingExample]) -> None:
        """Load historical data used during feature computation.

        Args:
            examples: All available historical games; the extractor will
                filter to ``outcome.final_at < as_of`` at extract time.
        """
        ...

    def extract(
        self,
        event_id: str,
        home_team: str,
        away_team: str,
        as_of: datetime,
    ) -> FeatureSet:
        """Compute features using only data available before ``as_of``.

        Args:
            event_id: Identifier for the game being predicted.
            home_team: Home team identifier.
            away_team: Away team identifier.
            as_of: Hard cutoff; no feature may use data after this timestamp.

        Returns:
            A FeatureSet ready for passing to ``Model.predict``.
        """
        ...
