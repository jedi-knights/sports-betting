"""Tests for the ensemble model that averages predictions from multiple models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bet.modeling.elo import EloModel
from bet.modeling.ensemble import EnsembleModel
from bet.modeling.logistic import LogisticRegressionModel
from bet.modeling.types import (
    ActualOutcome,
    FeatureSet,
    ProbabilityEstimate,
    TrainingExample,
)


def _dt(day: int) -> datetime:
    return datetime(2024, 1, day, tzinfo=UTC)


def _make_example(
    home_elo: float,
    away_elo: float,
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
            home_team="chiefs",
            away_team="bears",
            as_of=dt,
            features={
                "home_elo": home_elo,
                "away_elo": away_elo,
                "elo_diff": elo_diff,
            },
        ),
        outcome=ActualOutcome(
            event_id=f"game-{day}",
            home_score=home_score,
            away_score=away_score,
            final_at=dt,
        ),
    )


def _predict_features(elo_diff: float) -> FeatureSet:
    home = 1500.0 + elo_diff / 2
    away = 1500.0 - elo_diff / 2
    return FeatureSet(
        event_id="pred",
        sport="nfl",
        home_team="chiefs",
        away_team="bears",
        as_of=datetime(2024, 2, 1, tzinfo=UTC),
        features={
            "home_elo": home,
            "away_elo": away,
            "elo_diff": elo_diff,
        },
    )


def _training_set() -> list[TrainingExample]:
    return [_make_example(1600.0, 1400.0, 200.0, 28, 14, i) for i in range(1, 11)] + [
        _make_example(1400.0, 1600.0, -200.0, 10, 27, i) for i in range(11, 21)
    ]


class TestEnsembleModelBasics:
    def test_predict_raises_when_no_models(self) -> None:
        # Arrange
        model = EnsembleModel([])

        # Act / Assert
        with pytest.raises(ValueError, match="at least one model"):
            model.predict(_predict_features(0.0))

    def test_predict_returns_probability_estimate(self) -> None:
        # Arrange
        model = EnsembleModel([EloModel(), LogisticRegressionModel()])
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(100.0))

        # Assert
        assert isinstance(result, ProbabilityEstimate)

    def test_probabilities_sum_to_one(self) -> None:
        # Arrange
        model = EnsembleModel([EloModel(), LogisticRegressionModel()])
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(100.0))

        # Assert
        draw = result.draw or 0.0
        assert abs(result.home_win + result.away_win + draw - 1.0) < 1e-6

    def test_model_id_is_ensemble(self) -> None:
        # Arrange
        model = EnsembleModel([EloModel()])
        model.fit(_training_set())

        # Act
        result = model.predict(_predict_features(0.0))

        # Assert
        assert result.model_id == "ensemble"

    def test_single_model_ensemble_matches_base_model(self) -> None:
        # Arrange
        elo = EloModel()
        elo.fit(_training_set())
        ensemble = EnsembleModel([EloModel()])
        ensemble.fit(_training_set())

        features = _predict_features(100.0)

        # Act
        expected = elo.predict(features)
        result = ensemble.predict(features)

        # Assert — single-model ensemble must reproduce the base model output
        assert abs(result.home_win - expected.home_win) < 1e-9

    def test_positive_elo_diff_favours_home_win(self) -> None:
        # Arrange
        model = EnsembleModel([EloModel(), LogisticRegressionModel()])
        model.fit(_training_set())

        # Act
        strong_home = model.predict(_predict_features(200.0))
        weak_home = model.predict(_predict_features(-200.0))

        # Assert
        assert strong_home.home_win > weak_home.home_win

    def test_fit_propagates_to_all_component_models(self) -> None:
        # Arrange — fit one set of examples, then predict; ensemble should reflect
        # both models having been trained on the same data
        examples = _training_set()
        elo = EloModel()
        logistic = LogisticRegressionModel()
        ensemble = EnsembleModel([elo, logistic])
        ensemble.fit(examples)

        # Act — both component models are now fitted; predict should not raise
        result = ensemble.predict(_predict_features(50.0))

        # Assert
        assert 0.0 < result.home_win < 1.0
