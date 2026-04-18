"""Tests for the logistic regression model."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sklearn.exceptions import NotFittedError

from bet.modeling.logistic import LogisticRegressionModel
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
    dt = datetime(2023, 9, day, tzinfo=UTC)
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
        as_of=datetime(2023, 10, 1, tzinfo=UTC),
        features={"elo_diff": elo_diff},
    )


def _build_training_data() -> list[TrainingExample]:
    """Synthetic data: large positive elo_diff → home win; large negative → away win."""
    examples = []
    day = 1
    for _ in range(10):
        examples.append(_make_example(elo_diff=200.0, home_score=3, away_score=1, day=day))
        day += 1
    for _ in range(10):
        examples.append(_make_example(elo_diff=-200.0, home_score=1, away_score=3, day=day))
        day += 1
    return examples


class TestLogisticRegressionFit:
    def test_fit_empty_raises(self) -> None:
        model = LogisticRegressionModel()
        with pytest.raises(ValueError, match="fit requires"):
            model.fit([])

    def test_fit_succeeds_with_data(self) -> None:
        model = LogisticRegressionModel()
        model.fit(_build_training_data())
        assert model._fitted

    def test_predict_before_fit_raises(self) -> None:
        model = LogisticRegressionModel()
        with pytest.raises(NotFittedError):
            model.predict(_predict_features(0.0))


class TestLogisticRegressionPredict:
    def setup_method(self) -> None:
        self.model = LogisticRegressionModel()
        self.model.fit(_build_training_data())

    def test_returns_probability_estimate(self) -> None:
        result = self.model.predict(_predict_features(100.0))
        assert isinstance(result, ProbabilityEstimate)

    def test_probabilities_sum_to_one(self) -> None:
        result = self.model.predict(_predict_features(100.0))
        total = result.home_win + result.away_win + (result.draw or 0.0)
        assert abs(total - 1.0) < 1e-9

    def test_all_probabilities_in_range(self) -> None:
        result = self.model.predict(_predict_features(100.0))
        assert 0.0 <= result.home_win <= 1.0
        assert 0.0 <= result.away_win <= 1.0

    def test_draw_is_none_for_binary_data(self) -> None:
        # Training data has no draws, so draw should not appear in classes
        result = self.model.predict(_predict_features(0.0))
        assert result.draw is None

    def test_positive_elo_diff_favors_home(self) -> None:
        result = self.model.predict(_predict_features(200.0))
        assert result.home_win > result.away_win

    def test_negative_elo_diff_favors_away(self) -> None:
        result = self.model.predict(_predict_features(-200.0))
        assert result.away_win > result.home_win

    def test_model_id_is_set(self) -> None:
        result = self.model.predict(_predict_features(0.0))
        assert result.model_id == "logistic_regression"


class TestLogisticRegressionScaling:
    def test_scaler_is_fitted_after_fit(self) -> None:
        """StandardScaler.mean_ must exist after fit — proves fit_transform was called.

        Without calling fit_transform in fit(), mean_ is never set.
        """
        # Arrange / Act
        model = LogisticRegressionModel()
        model.fit(_build_training_data())

        # Assert
        assert hasattr(model._scaler, "mean_"), (
            "StandardScaler.mean_ not set — fit_transform() was never called in fit()"
        )

    def test_predictions_correct_with_elo_scale_features(self) -> None:
        """Model must predict correctly when features have Elo-magnitude values (~1500).

        Without scaling, lbfgs struggles because home_elo (~1500) dominates gradients
        and form (~0.0–1.0) features are nearly invisible.
        """

        # Arrange — home team is a strong favourite on both Elo and form
        def _multiscale_example(
            home_elo: float,
            away_elo: float,
            home_form: float,
            away_form: float,
            home_score: int,
            away_score: int,
            day: int,
        ) -> TrainingExample:
            dt = datetime(2023, 9, day, tzinfo=UTC)
            return TrainingExample(
                feature_set=FeatureSet(
                    event_id=f"ms-{day}",
                    sport="nfl",
                    home_team="home",
                    away_team="away",
                    as_of=dt,
                    features={
                        "home_elo": home_elo,
                        "away_elo": away_elo,
                        "home_form_5": home_form,
                        "away_form_5": away_form,
                    },
                ),
                outcome=ActualOutcome(
                    event_id=f"ms-{day}",
                    home_score=home_score,
                    away_score=away_score,
                    final_at=dt,
                ),
            )

        examples = []
        for i in range(10):
            examples.append(_multiscale_example(1600.0, 1400.0, 0.8, 0.2, 3, 1, day=i + 1))
        for i in range(10, 20):
            examples.append(_multiscale_example(1400.0, 1600.0, 0.2, 0.8, 1, 3, day=i + 1))

        model = LogisticRegressionModel()
        model.fit(examples)

        # Act — strong home favourite
        feat = FeatureSet(
            event_id="pred",
            sport="nfl",
            home_team="home",
            away_team="away",
            as_of=datetime(2023, 10, 1, tzinfo=UTC),
            features={
                "home_elo": 1600.0,
                "away_elo": 1400.0,
                "home_form_5": 0.8,
                "away_form_5": 0.2,
            },
        )
        result = model.predict(feat)

        # Assert
        assert result.home_win > result.away_win


class TestLogisticRegressionWithDraws:
    def test_draw_not_none_when_draws_in_training_data(self) -> None:
        examples = [
            _make_example(elo_diff=200.0, home_score=3, away_score=1, day=1),
            _make_example(elo_diff=-200.0, home_score=1, away_score=3, day=2),
            _make_example(elo_diff=0.0, home_score=1, away_score=1, day=3),
            _make_example(elo_diff=100.0, home_score=2, away_score=0, day=4),
            _make_example(elo_diff=-100.0, home_score=0, away_score=2, day=5),
        ]
        model = LogisticRegressionModel()
        model.fit(examples)
        result = model.predict(_predict_features(0.0))
        assert result.draw is not None
        total = result.home_win + result.away_win + result.draw
        assert abs(total - 1.0) < 1e-9
