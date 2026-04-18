"""Tests for the Elo rating model."""

from __future__ import annotations

from datetime import UTC, datetime

from bet.modeling.elo import EloModel
from bet.modeling.types import (
    ActualOutcome,
    FeatureSet,
    ProbabilityEstimate,
    TrainingExample,
)


def _make_example(
    event_id: str,
    home: str,
    away: str,
    home_score: int,
    away_score: int,
    day: int,
) -> TrainingExample:
    as_of = datetime(2023, 9, day, tzinfo=UTC)
    return TrainingExample(
        feature_set=FeatureSet(
            event_id=event_id,
            sport="nfl",
            home_team=home,
            away_team=away,
            as_of=as_of,
        ),
        outcome=ActualOutcome(
            event_id=event_id,
            home_score=home_score,
            away_score=away_score,
            final_at=as_of,
        ),
    )


def _predict_features(home: str, away: str, home_elo: float, away_elo: float) -> FeatureSet:
    return FeatureSet(
        event_id="pred",
        sport="nfl",
        home_team=home,
        away_team=away,
        as_of=datetime(2023, 9, 30, tzinfo=UTC),
        features={
            "home_elo": home_elo,
            "away_elo": away_elo,
            "elo_diff": home_elo - away_elo,
        },
    )


class TestEloRatingUpdates:
    def test_winner_gains_rating(self) -> None:
        model = EloModel(home_advantage=0.0)
        before = model.rating("chiefs")
        model.update("chiefs", "bears", 24, 10)
        assert model.rating("chiefs") > before

    def test_loser_loses_rating(self) -> None:
        model = EloModel(home_advantage=0.0)
        before = model.rating("bears")
        model.update("chiefs", "bears", 24, 10)
        assert model.rating("bears") < before

    def test_rating_change_is_symmetric(self) -> None:
        model = EloModel(home_advantage=0.0)
        model.update("chiefs", "bears", 24, 10)
        chiefs_gain = model.rating("chiefs") - 1500.0
        bears_loss = 1500.0 - model.rating("bears")
        assert abs(chiefs_gain - bears_loss) < 1e-9

    def test_draw_produces_no_change_for_equal_teams(self) -> None:
        model = EloModel(home_advantage=0.0)
        model.update("a", "b", 1, 1)
        assert abs(model.rating("a") - 1500.0) < 1e-9
        assert abs(model.rating("b") - 1500.0) < 1e-9

    def test_unknown_team_returns_initial_rating(self) -> None:
        model = EloModel(initial_rating=1500.0)
        assert model.rating("unknown") == 1500.0

    def test_custom_initial_rating(self) -> None:
        model = EloModel(initial_rating=1000.0)
        assert model.rating("new_team") == 1000.0


class TestEloExpectedScore:
    def test_equal_ratings_give_half(self) -> None:
        model = EloModel()
        assert abs(model.expected_score(1500.0, 1500.0) - 0.5) < 1e-9

    def test_higher_rating_gives_more_than_half(self) -> None:
        model = EloModel()
        assert model.expected_score(1600.0, 1500.0) > 0.5

    def test_400_point_gap_gives_approx_91_percent(self) -> None:
        model = EloModel()
        # 10^(400/400) = 10, so E = 1/(1+10) ≈ 0.0909 for underdog
        assert abs(model.expected_score(1100.0, 1500.0) - (1.0 / 11.0)) < 1e-9


class TestEloFit:
    def test_fit_processes_in_chronological_order(self) -> None:
        # Provide examples out of order; fit must sort before processing
        examples = [
            _make_example("g2", "bears", "packers", 21, 14, day=14),
            _make_example("g1", "chiefs", "bears", 24, 10, day=7),
        ]
        model = EloModel(home_advantage=0.0)
        model.fit(examples)
        # Chiefs beat Bears, then Bears beat Packers — Bears should have
        # recovered some of what they lost to Chiefs
        assert model.rating("chiefs") > 1500.0
        assert model.rating("packers") < 1500.0

    def test_fit_empty_examples_leaves_ratings_unchanged(self) -> None:
        model = EloModel()
        model.fit([])
        assert model.rating("anyone") == 1500.0


class TestEloMarginOfVictory:
    def test_blowout_produces_more_rating_change_than_close_win(self) -> None:
        # Arrange
        model_close = EloModel(home_advantage=0.0, use_mov=True)
        model_blowout = EloModel(home_advantage=0.0, use_mov=True)

        # Act
        model_close.update("TeamA", "TeamB", 17, 16)
        model_blowout.update("TeamA", "TeamB", 42, 7)

        # Assert
        assert model_blowout.rating("TeamA") > model_close.rating("TeamA")
        assert model_blowout.rating("TeamB") < model_close.rating("TeamB")

    def test_use_mov_false_gives_same_change_regardless_of_margin(self) -> None:
        # Arrange
        model_close = EloModel(home_advantage=0.0, use_mov=False)
        model_blowout = EloModel(home_advantage=0.0, use_mov=False)

        # Act
        model_close.update("TeamA", "TeamB", 17, 16)
        model_blowout.update("TeamA", "TeamB", 42, 7)

        # Assert — same K regardless of margin
        assert abs(model_close.rating("TeamA") - model_blowout.rating("TeamA")) < 1e-9
        assert abs(model_close.rating("TeamB") - model_blowout.rating("TeamB")) < 1e-9

    def test_draw_is_unaffected_by_mov(self) -> None:
        # Arrange — equal teams, draw result, mov=True
        model = EloModel(home_advantage=0.0, use_mov=True)

        # Act
        model.update("TeamA", "TeamB", 14, 14)

        # Assert — draw with equal teams gives no rating change
        assert abs(model.rating("TeamA") - 1500.0) < 1e-9
        assert abs(model.rating("TeamB") - 1500.0) < 1e-9

    def test_symmetry_preserved_with_mov(self) -> None:
        # Arrange
        model = EloModel(home_advantage=0.0, use_mov=True)

        # Act
        model.update("TeamA", "TeamB", 35, 7)

        # Assert — winner gains exactly what loser drops
        gain = model.rating("TeamA") - 1500.0
        loss = 1500.0 - model.rating("TeamB")
        assert abs(gain - loss) < 1e-9


class TestEloPredict:
    def test_predict_returns_probability_estimate(self) -> None:
        model = EloModel()
        features = _predict_features("chiefs", "bears", 1560.0, 1480.0)
        result = model.predict(features)
        assert isinstance(result, ProbabilityEstimate)

    def test_predict_probabilities_sum_to_one(self) -> None:
        model = EloModel()
        features = _predict_features("chiefs", "bears", 1560.0, 1480.0)
        result = model.predict(features)
        assert abs(result.home_win + result.away_win - 1.0) < 1e-9

    def test_predict_draw_is_none(self) -> None:
        model = EloModel()
        features = _predict_features("chiefs", "bears", 1560.0, 1480.0)
        assert model.predict(features).draw is None

    def test_higher_rated_team_has_higher_win_prob(self) -> None:
        model = EloModel(home_advantage=0.0)
        features = _predict_features("a", "b", 1600.0, 1400.0)
        result = model.predict(features)
        assert result.home_win > result.away_win

    def test_equal_ratings_with_home_advantage_favors_home(self) -> None:
        model = EloModel(home_advantage=65.0)
        features = _predict_features("a", "b", 1500.0, 1500.0)
        result = model.predict(features)
        assert result.home_win > 0.5

    def test_predict_uses_correct_event_id(self) -> None:
        model = EloModel()
        features = _predict_features("a", "b", 1500.0, 1500.0)
        features.event_id = "specific-event"
        assert model.predict(features).event_id == "specific-event"
