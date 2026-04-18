"""Tests for the NFL Elo feature extractor."""

from __future__ import annotations

from datetime import UTC, datetime

from bet.features.nfl import NFLFeatureExtractor
from bet.modeling.types import ActualOutcome, FeatureSet, TrainingExample


def _dt(day: int) -> datetime:
    return datetime(2023, 9, day, tzinfo=UTC)


def _make_example(
    home: str,
    away: str,
    home_score: int,
    away_score: int,
    day: int,
) -> TrainingExample:
    dt = _dt(day)
    return TrainingExample(
        feature_set=FeatureSet(
            event_id=f"game-{day}",
            sport="nfl",
            home_team=home,
            away_team=away,
            as_of=dt,
        ),
        outcome=ActualOutcome(
            event_id=f"game-{day}",
            home_score=home_score,
            away_score=away_score,
            final_at=dt,
        ),
    )


class TestNFLFeatureExtractorBasics:
    def test_extract_returns_feature_set(self) -> None:
        extractor = NFLFeatureExtractor()
        extractor.fit([])
        result = extractor.extract("game-1", "chiefs", "bears", _dt(7))
        assert isinstance(result, FeatureSet)

    def test_extract_includes_home_elo(self) -> None:
        extractor = NFLFeatureExtractor()
        extractor.fit([])
        result = extractor.extract("game-1", "chiefs", "bears", _dt(7))
        assert "home_elo" in result.features

    def test_extract_includes_away_elo(self) -> None:
        extractor = NFLFeatureExtractor()
        extractor.fit([])
        result = extractor.extract("game-1", "chiefs", "bears", _dt(7))
        assert "away_elo" in result.features

    def test_extract_includes_elo_diff(self) -> None:
        extractor = NFLFeatureExtractor()
        extractor.fit([])
        result = extractor.extract("game-1", "chiefs", "bears", _dt(7))
        assert "elo_diff" in result.features

    def test_elo_diff_equals_home_minus_away(self) -> None:
        extractor = NFLFeatureExtractor()
        extractor.fit([])
        result = extractor.extract("game-1", "chiefs", "bears", _dt(7))
        expected_diff = result.features["home_elo"] - result.features["away_elo"]
        assert abs(result.features["elo_diff"] - expected_diff) < 1e-9

    def test_unknown_teams_get_initial_rating(self) -> None:
        extractor = NFLFeatureExtractor(initial_rating=1500.0)
        extractor.fit([])
        result = extractor.extract("game-1", "unknown_a", "unknown_b", _dt(7))
        assert result.features["home_elo"] == 1500.0
        assert result.features["away_elo"] == 1500.0

    def test_sport_is_nfl(self) -> None:
        extractor = NFLFeatureExtractor()
        extractor.fit([])
        result = extractor.extract("game-1", "a", "b", _dt(7))
        assert result.sport == "nfl"


class TestNFLFeatureExtractorLookahead:
    def test_game_before_as_of_is_used(self) -> None:
        extractor = NFLFeatureExtractor(home_advantage=0.0)
        examples = [_make_example("chiefs", "bears", 24, 10, day=7)]
        extractor.fit(examples)
        # as_of is day 14 — game on day 7 should be included
        result = extractor.extract("g", "chiefs", "bears", _dt(14))
        # Chiefs won, so their rating > initial
        assert result.features["home_elo"] > 1500.0

    def test_game_at_as_of_is_excluded(self) -> None:
        extractor = NFLFeatureExtractor(home_advantage=0.0)
        examples = [_make_example("chiefs", "bears", 24, 10, day=7)]
        extractor.fit(examples)
        # as_of is exactly day 7 — the game itself should NOT be included
        result = extractor.extract("g", "chiefs", "bears", _dt(7))
        assert result.features["home_elo"] == 1500.0

    def test_game_after_as_of_is_excluded(self) -> None:
        extractor = NFLFeatureExtractor(home_advantage=0.0)
        examples = [_make_example("chiefs", "bears", 24, 10, day=14)]
        extractor.fit(examples)
        # as_of is day 7 — game on day 14 is in the future, must not be used
        result = extractor.extract("g", "chiefs", "bears", _dt(7))
        assert result.features["home_elo"] == 1500.0

    def test_only_past_games_affect_ratings(self) -> None:
        extractor = NFLFeatureExtractor(home_advantage=0.0)
        examples = [
            _make_example("chiefs", "bears", 24, 10, day=7),  # chiefs win
            _make_example("chiefs", "bears", 10, 24, day=21),  # bears win (future)
        ]
        extractor.fit(examples)
        # as_of is day 14 — only game 1 is available
        result = extractor.extract("g", "chiefs", "bears", _dt(14))
        # chiefs still benefiting from day-7 win
        assert result.features["home_elo"] > 1500.0


class TestNFLFeatureExtractorRatingAccumulation:
    def test_consistent_winner_has_higher_rating(self) -> None:
        extractor = NFLFeatureExtractor(home_advantage=0.0)
        examples = [
            _make_example("a", "b", 3, 0, day=1),
            _make_example("a", "c", 3, 0, day=2),
            _make_example("a", "d", 3, 0, day=3),
        ]
        extractor.fit(examples)
        result = extractor.extract("g", "a", "b", _dt(10))
        assert result.features["home_elo"] > 1500.0

    def test_consistent_loser_has_lower_rating(self) -> None:
        extractor = NFLFeatureExtractor(home_advantage=0.0)
        examples = [
            _make_example("a", "b", 0, 3, day=1),
            _make_example("c", "b", 3, 0, day=2),
            _make_example("d", "b", 3, 0, day=3),
        ]
        extractor.fit(examples)
        result = extractor.extract("g", "a", "b", _dt(10))
        assert result.features["away_elo"] < 1500.0
