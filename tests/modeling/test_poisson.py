"""Tests for the Poisson goal prediction model."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

from bet.modeling.poisson import PoissonModel
from bet.modeling.types import (
    ActualOutcome,
    FeatureSet,
    TrainingExample,
)


def _make_example(
    home: str,
    away: str,
    home_score: int,
    away_score: int,
    day: int,
) -> TrainingExample:
    dt = datetime(2023, 8, day, tzinfo=UTC)
    eid = f"{home}-{away}-{day}"
    return TrainingExample(
        feature_set=FeatureSet(
            event_id=eid, sport="soccer", home_team=home, away_team=away, as_of=dt
        ),
        outcome=ActualOutcome(
            event_id=eid, home_score=home_score, away_score=away_score, final_at=dt
        ),
    )


def _predict_features(
    home_attack: float = 1.0,
    home_defense: float = 1.0,
    away_attack: float = 1.0,
    away_defense: float = 1.0,
) -> FeatureSet:
    return FeatureSet(
        event_id="pred",
        sport="soccer",
        home_team="home",
        away_team="away",
        as_of=datetime(2023, 9, 1, tzinfo=UTC),
        features={
            "home_attack": home_attack,
            "home_defense": home_defense,
            "away_attack": away_attack,
            "away_defense": away_defense,
        },
    )


_SAMPLE_GAMES = [
    _make_example("arsenal", "chelsea", 2, 1, day=1),
    _make_example("chelsea", "liverpool", 1, 1, day=2),
    _make_example("liverpool", "arsenal", 3, 1, day=3),
    _make_example("arsenal", "liverpool", 0, 2, day=4),
    _make_example("chelsea", "arsenal", 2, 0, day=5),
    _make_example("liverpool", "chelsea", 1, 0, day=6),
    _make_example("arsenal", "chelsea", 1, 1, day=7),
    _make_example("chelsea", "liverpool", 2, 3, day=8),
    _make_example("liverpool", "arsenal", 2, 2, day=9),
    _make_example("arsenal", "liverpool", 1, 0, day=10),
]


class TestPoissonFit:
    def test_fit_empty_leaves_defaults(self) -> None:
        model = PoissonModel()
        model.fit([])
        assert model._home_baseline == 1.5
        assert model._away_baseline == 1.1

    def test_fit_estimates_baselines_from_data(self) -> None:
        model = PoissonModel()
        model.fit(_SAMPLE_GAMES)
        home_goals = [ex.outcome.home_score for ex in _SAMPLE_GAMES]
        away_goals = [ex.outcome.away_score for ex in _SAMPLE_GAMES]
        assert abs(model._home_baseline - sum(home_goals) / len(home_goals)) < 1e-9
        assert abs(model._away_baseline - sum(away_goals) / len(away_goals)) < 1e-9


class TestPoissonPredict:
    def test_probabilities_sum_to_one(self) -> None:
        model = PoissonModel()
        result = model.predict(_predict_features())
        total = result.home_win + result.away_win + (result.draw or 0.0)
        assert abs(total - 1.0) < 1e-9

    def test_draw_is_not_none(self) -> None:
        model = PoissonModel()
        result = model.predict(_predict_features())
        assert result.draw is not None

    def test_all_probabilities_positive(self) -> None:
        model = PoissonModel()
        result = model.predict(_predict_features())
        assert result.home_win > 0.0
        assert result.away_win > 0.0
        assert result.draw > 0.0  # type: ignore[operator]

    def test_stronger_attack_raises_win_probability(self) -> None:
        model = PoissonModel()
        base = model.predict(_predict_features(home_attack=1.0, away_defense=1.0))
        strong = model.predict(_predict_features(home_attack=2.0, away_defense=1.5))
        assert strong.home_win > base.home_win

    def test_stronger_defense_lowers_opponent_win_prob(self) -> None:
        # Lower away_defense = away team concedes fewer goals = harder for home to win
        model = PoissonModel()
        weak_def = model.predict(_predict_features(away_defense=1.5))
        strong_def = model.predict(_predict_features(away_defense=0.5))
        assert strong_def.home_win < weak_def.home_win

    def test_home_favored_by_default_baselines(self) -> None:
        # Default home_baseline (1.5) > away_baseline (1.1), so home should win more
        model = PoissonModel()
        result = model.predict(_predict_features())
        assert result.home_win > result.away_win


class TestPoissonScoreMatrix:
    def test_score_matrix_shape(self) -> None:
        model = PoissonModel(max_goals=5)
        matrix = model._score_matrix(1.5, 1.1)
        assert matrix.shape == (6, 6)

    def test_score_matrix_sums_close_to_one(self) -> None:
        # Truncated at max_goals=10, so sum should be very close to 1
        model = PoissonModel(max_goals=10)
        matrix = model._score_matrix(1.5, 1.1)
        assert abs(matrix.sum() - 1.0) < 1e-3

    def test_dixon_coles_correction_changes_matrix(self) -> None:
        corrected = PoissonModel(rho=-0.13)._score_matrix(1.5, 1.1)
        uncorrected = PoissonModel(rho=0.0)._score_matrix(1.5, 1.1)
        assert not np.allclose(corrected, uncorrected)

    def test_home_win_in_lower_triangle(self) -> None:
        # row > col in the matrix = home scored more than away = home win
        model = PoissonModel()
        matrix = model._score_matrix(3.0, 0.5)
        home_win = float(np.sum(np.tril(matrix, -1)))
        # With lambda_home=3, lambda_away=0.5, home should win most often
        assert home_win > 0.5


class TestPoissonModelGuards:
    def test_negative_rho_accepted(self) -> None:
        # Arrange / Act / Assert — should not raise
        model = PoissonModel(rho=-0.13)
        assert model._rho == -0.13

    def test_positive_rho_raises(self) -> None:
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="rho must be"):
            PoissonModel(rho=0.5)

    def test_zero_rho_accepted(self) -> None:
        # Arrange / Act / Assert — rho=0 disables the correction; should be fine
        model = PoissonModel(rho=0.0)
        assert model._rho == 0.0

    def test_predict_raises_when_score_matrix_sum_nonpositive(self) -> None:
        """A subclass that returns a zero matrix should trigger the guard in predict."""

        # Arrange
        class _ZeroMatrixPoisson(PoissonModel):
            def _score_matrix(self, lh: float, la: float) -> np.ndarray:
                import numpy as _np

                return _np.zeros((self._max_goals + 1, self._max_goals + 1))

        model = _ZeroMatrixPoisson()
        features = FeatureSet(
            event_id="guard-test",
            sport="soccer",
            home_team="a",
            away_team="b",
            as_of=datetime(2024, 1, 1, tzinfo=UTC),
            features={
                "home_attack": 1.0,
                "home_defense": 1.0,
                "away_attack": 1.0,
                "away_defense": 1.0,
            },
        )

        # Act / Assert
        with pytest.raises(ValueError, match="score matrix sum"):
            model.predict(features)
