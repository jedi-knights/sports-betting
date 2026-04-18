"""Tests for the gradient boosting classification model."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sklearn.exceptions import NotFittedError

from bet.modeling.gradient_boosting import GradientBoostingModel
from bet.modeling.types import (
    ActualOutcome,
    FeatureSet,
    ProbabilityEstimate,
    TrainingExample,
)


def _make_example(
    elo_diff: float,
    home_score: int,
    away_score: int,
    day: int,
) -> TrainingExample:
    dt = datetime(2024, 1, day, tzinfo=UTC)
    return TrainingExample(
        feature_set=FeatureSet(
            event_id=f"game-{day}",
            sport="nfl",
            home_team="home",
            away_team="away",
            as_of=dt,
            features={"elo_diff": elo_diff},
        ),
        outcome=ActualOutcome(
            event_id=f"game-{day}",
            home_score=home_score,
            away_score=away_score,
            final_at=dt,
        ),
    )


def _predict_features(elo_diff: float) -> FeatureSet:
    return FeatureSet(
        event_id="pred",
        sport="nfl",
        home_team="home",
        away_team="away",
        as_of=datetime(2024, 2, 1, tzinfo=UTC),
        features={"elo_diff": elo_diff},
    )


def _training_set() -> list[TrainingExample]:
    return [_make_example(100.0, 28, 14, i) for i in range(1, 11)] + [
        _make_example(-100.0, 10, 27, i) for i in range(11, 21)
    ]


class TestGradientBoostingModelBasics:
    def test_predict_raises_before_fit(self) -> None:
        # Arrange
        model = GradientBoostingModel()

        # Act / Assert
        with pytest.raises(NotFittedError):
            model.predict(_predict_features(50.0))

    def test_fit_raises_on_empty_examples(self) -> None:
        # Arrange
        model = GradientBoostingModel()

        # Act / Assert
        with pytest.raises(ValueError, match="fit requires at least one"):
            model.fit([])

    def test_predict_returns_probability_estimate(self) -> None:
        # Arrange
        model = GradientBoostingModel()
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(50.0))

        # Assert
        assert isinstance(result, ProbabilityEstimate)

    def test_probabilities_sum_to_one(self) -> None:
        # Arrange
        model = GradientBoostingModel()
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(50.0))

        # Assert
        draw = result.draw or 0.0
        assert abs(result.home_win + result.away_win + draw - 1.0) < 1e-6

    def test_model_id_is_gradient_boosting(self) -> None:
        # Arrange
        model = GradientBoostingModel()
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(0.0))

        # Assert
        assert result.model_id == "gradient_boosting"

    def test_positive_elo_diff_increases_home_win_probability(self) -> None:
        # Arrange — train on clear home-advantage signal
        model = GradientBoostingModel()
        model.fit(_training_set())

        # Act
        high_home = model.predict(_predict_features(200.0))
        low_home = model.predict(_predict_features(-200.0))

        # Assert — stronger home team should have higher home_win probability
        assert high_home.home_win > low_home.home_win

    def test_no_draw_for_binary_sport(self) -> None:
        # Arrange — training data has only home_win / away_win labels
        model = GradientBoostingModel()
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(0.0))

        # Assert — no draws in NFL-style binary training data
        assert result.draw is None
