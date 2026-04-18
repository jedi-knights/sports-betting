"""Tests for the quantile regression model."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sklearn.exceptions import NotFittedError

from bet.modeling.quantile import QuantileRegressionModel
from bet.modeling.types import (
    ActualOutcome,
    FeatureSet,
    ProbabilityEstimate,
    TrainingExample,
)


def _dt(day: int) -> datetime:
    return datetime(2024, 1, day, tzinfo=UTC)


def _make_example(
    elo_diff: float,
    home_score: int,
    away_score: int,
    day: int,
) -> TrainingExample:
    dt = _dt(day)
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
    # Strong home signal: positive elo_diff → home wins by large margin
    return [_make_example(100.0, 28, 14, i) for i in range(1, 11)] + [
        _make_example(-100.0, 10, 27, i) for i in range(11, 21)
    ]


class TestQuantileRegressionModelBasics:
    def test_predict_raises_before_fit(self) -> None:
        # Arrange
        model = QuantileRegressionModel()

        # Act / Assert
        with pytest.raises(NotFittedError):
            model.predict(_predict_features(0.0))

    def test_fit_raises_on_empty_examples(self) -> None:
        # Arrange
        model = QuantileRegressionModel()

        # Act / Assert
        with pytest.raises(ValueError, match="fit requires at least one"):
            model.fit([])

    def test_predict_returns_probability_estimate(self) -> None:
        # Arrange
        model = QuantileRegressionModel()
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(0.0))

        # Assert
        assert isinstance(result, ProbabilityEstimate)

    def test_home_and_away_win_sum_to_one(self) -> None:
        # Arrange — quantile model outputs binary win probabilities (no draws)
        model = QuantileRegressionModel()
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(50.0))

        # Assert
        assert result.draw is None
        assert abs(result.home_win + result.away_win - 1.0) < 1e-6

    def test_model_id_is_quantile_regression(self) -> None:
        # Arrange
        model = QuantileRegressionModel()
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(0.0))

        # Assert
        assert result.model_id == "quantile_regression"

    def test_probabilities_in_valid_range(self) -> None:
        # Arrange
        model = QuantileRegressionModel()
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(50.0))

        # Assert
        assert 0.0 < result.home_win < 1.0
        assert 0.0 < result.away_win < 1.0

    def test_stronger_home_team_has_higher_win_probability(self) -> None:
        # Arrange — training data encodes a clear positive correlation between
        # elo_diff and home margin (positive elo_diff → home wins big)
        model = QuantileRegressionModel()
        model.fit(_training_set())

        # Act
        strong_home = model.predict(_predict_features(200.0))
        weak_home = model.predict(_predict_features(-200.0))

        # Assert
        assert strong_home.home_win > weak_home.home_win
