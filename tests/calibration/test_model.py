"""Tests for CalibratedModel wrapper."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sklearn.exceptions import NotFittedError

from bet.calibration.model import CalibratedModel
from bet.calibration.platt import PlattScaler
from bet.modeling.logistic import LogisticRegressionModel
from bet.modeling.poisson import PoissonModel
from bet.modeling.types import (
    ActualOutcome,
    FeatureSet,
    ProbabilityEstimate,
    TrainingExample,
)


def _dt(day: int) -> datetime:
    return datetime(2023, 9, day, tzinfo=UTC)


def _make_lr_example(
    elo_diff: float, home_score: int, away_score: int, day: int
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


def _lr_training_data() -> list[TrainingExample]:
    examples = []
    day = 1
    for _ in range(10):
        examples.append(_make_lr_example(200.0, 3, 1, day))
        day += 1
    for _ in range(10):
        examples.append(_make_lr_example(-200.0, 1, 3, day))
        day += 1
    return examples


def _lr_features(elo_diff: float) -> FeatureSet:
    return FeatureSet(
        event_id="pred",
        sport="nfl",
        home_team="home",
        away_team="away",
        as_of=datetime(2023, 10, 1, tzinfo=UTC),
        features={"elo_diff": elo_diff},
    )


def _soccer_features(
    home_attack: float = 1.5,
    away_defense: float = 0.8,
) -> FeatureSet:
    return FeatureSet(
        event_id="soccer-pred",
        sport="soccer",
        home_team="arsenal",
        away_team="chelsea",
        as_of=datetime(2023, 10, 1, tzinfo=UTC),
        features={
            "home_attack": home_attack,
            "home_defense": 1.0,
            "away_attack": 1.0,
            "away_defense": away_defense,
        },
    )


def _make_fitted_binary_model() -> CalibratedModel:
    """CalibratedModel wrapping LogisticRegressionModel, fully fitted."""
    examples = _lr_training_data()
    inner = LogisticRegressionModel()
    inner.fit(examples)

    probs = [inner.predict(ex.feature_set).home_win for ex in examples]
    outcomes = [1 if ex.outcome.home_score > ex.outcome.away_score else 0 for ex in examples]
    model = CalibratedModel(inner, PlattScaler())
    model.fit_calibrator(probs, outcomes)
    return model


class TestCalibratedModelFitCalibrator:
    def test_predict_before_fit_calibrator_raises(self) -> None:
        inner = LogisticRegressionModel()
        inner.fit(_lr_training_data())
        model = CalibratedModel(inner, PlattScaler())
        with pytest.raises(NotFittedError):
            model.predict(_lr_features(100.0))

    def test_fit_delegates_to_inner_model(self) -> None:
        inner = LogisticRegressionModel()
        model = CalibratedModel(inner, PlattScaler())
        model.fit(_lr_training_data())
        assert inner._fitted


class TestCalibratedModelPredict:
    def test_returns_probability_estimate(self) -> None:
        model = _make_fitted_binary_model()
        result = model.predict(_lr_features(100.0))
        assert isinstance(result, ProbabilityEstimate)

    def test_probabilities_sum_to_one_binary(self) -> None:
        model = _make_fitted_binary_model()
        result = model.predict(_lr_features(100.0))
        assert abs(result.home_win + result.away_win - 1.0) < 1e-9

    def test_draw_is_none_for_binary_sport(self) -> None:
        model = _make_fitted_binary_model()
        result = model.predict(_lr_features(0.0))
        assert result.draw is None

    def test_all_probabilities_in_range(self) -> None:
        model = _make_fitted_binary_model()
        result = model.predict(_lr_features(100.0))
        assert 0.0 <= result.home_win <= 1.0
        assert 0.0 <= result.away_win <= 1.0

    def test_model_id_contains_calibrated(self) -> None:
        model = _make_fitted_binary_model()
        result = model.predict(_lr_features(0.0))
        assert "calibrated" in result.model_id

    def test_event_id_preserved(self) -> None:
        model = _make_fitted_binary_model()
        features = _lr_features(0.0)
        features.event_id = "specific-game"
        result = model.predict(features)
        assert result.event_id == "specific-game"

    def test_positive_elo_diff_favors_home(self) -> None:
        model = _make_fitted_binary_model()
        result = model.predict(_lr_features(200.0))
        assert result.home_win > result.away_win

    def test_negative_elo_diff_favors_away(self) -> None:
        model = _make_fitted_binary_model()
        result = model.predict(_lr_features(-200.0))
        assert result.away_win > result.home_win


class TestCalibratedModelWithDraw:
    def test_draw_not_none_for_soccer_model(self) -> None:
        poisson = PoissonModel()
        features = _soccer_features()

        raw_probs = [poisson.predict(_soccer_features(ha, 1.0)).home_win for ha in [0.5, 2.0]]
        outcomes = [0, 1]

        model = CalibratedModel(poisson, PlattScaler())
        model.fit_calibrator(raw_probs, outcomes)

        result = model.predict(features)
        assert result.draw is not None

    def test_probabilities_sum_to_one_with_draw(self) -> None:
        poisson = PoissonModel()
        raw_probs = [poisson.predict(_soccer_features(ha, 1.0)).home_win for ha in [0.5, 2.0]]
        outcomes = [0, 1]

        model = CalibratedModel(poisson, PlattScaler())
        model.fit_calibrator(raw_probs, outcomes)

        result = model.predict(_soccer_features())
        total = result.home_win + result.away_win + (result.draw or 0.0)
        assert abs(total - 1.0) < 1e-9
