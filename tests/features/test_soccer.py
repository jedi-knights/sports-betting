"""Tests for the soccer strength feature extractor."""

from __future__ import annotations

from datetime import UTC, datetime

from bet.features.epl import EPLFeatureExtractor as SoccerFeatureExtractor
from bet.modeling.types import ActualOutcome, FeatureSet, TrainingExample


def _dt(day: int) -> datetime:
    return datetime(2023, 8, day, tzinfo=UTC)


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
            sport="epl",
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


class TestSoccerFeatureExtractorBasics:
    def test_extract_returns_feature_set(self) -> None:
        ext = SoccerFeatureExtractor()
        ext.fit([])
        result = ext.extract("g", "a", "b", _dt(10))
        assert isinstance(result, FeatureSet)

    def test_extract_returns_all_four_features(self) -> None:
        ext = SoccerFeatureExtractor()
        ext.fit([])
        result = ext.extract("g", "a", "b", _dt(10))
        for key in ("home_attack", "home_defense", "away_attack", "away_defense"):
            assert key in result.features, f"missing feature: {key}"

    def test_unknown_teams_return_default_strength(self) -> None:
        ext = SoccerFeatureExtractor()
        ext.fit([])
        result = ext.extract("g", "unknown_a", "unknown_b", _dt(10))
        assert result.features["home_attack"] == 1.0
        assert result.features["home_defense"] == 1.0
        assert result.features["away_attack"] == 1.0
        assert result.features["away_defense"] == 1.0

    def test_sport_is_soccer(self) -> None:
        ext = SoccerFeatureExtractor()
        ext.fit([])
        result = ext.extract("g", "a", "b", _dt(10))
        assert result.sport == "epl"

    def test_all_features_positive(self) -> None:
        ext = SoccerFeatureExtractor()
        examples = [
            _make_example("arsenal", "chelsea", 2, 1, day=1),
            _make_example("chelsea", "arsenal", 1, 2, day=2),
        ]
        ext.fit(examples)
        result = ext.extract("g", "arsenal", "chelsea", _dt(10))
        for k, v in result.features.items():
            assert v > 0.0, f"{k}={v} is not positive"


class TestSoccerFeatureExtractorLookahead:
    def test_game_at_as_of_is_excluded(self) -> None:
        ext = SoccerFeatureExtractor()
        examples = [_make_example("arsenal", "chelsea", 3, 0, day=5)]
        ext.fit(examples)
        # as_of is exactly day 5 — game must not be included
        result = ext.extract("g", "arsenal", "chelsea", _dt(5))
        assert result.features["home_attack"] == 1.0  # no history

    def test_game_before_as_of_is_used(self) -> None:
        ext = SoccerFeatureExtractor()
        examples = [_make_example("arsenal", "chelsea", 3, 0, day=5)]
        ext.fit(examples)
        # as_of is day 10 — game on day 5 should be included
        result = ext.extract("g", "arsenal", "chelsea", _dt(10))
        assert result.features["home_attack"] != 1.0  # history now available

    def test_future_game_does_not_contaminate_features(self) -> None:
        ext = SoccerFeatureExtractor()
        examples = [
            _make_example("arsenal", "chelsea", 1, 1, day=5),  # past
            _make_example("arsenal", "chelsea", 5, 0, day=20),  # future
        ]
        ext.fit(examples)
        # as_of is day 10 — only day 5 should count
        result_day10 = ext.extract("g", "arsenal", "chelsea", _dt(10))
        result_day25 = ext.extract("g", "arsenal", "chelsea", _dt(25))
        # Day 25 has more data available → different features
        assert result_day10.features != result_day25.features


class TestSoccerFeatureExtractorStrengthCalculation:
    def test_high_scorer_has_higher_attack_strength(self) -> None:
        ext = SoccerFeatureExtractor()
        examples = [
            # Arsenal scores 3 per game
            _make_example("arsenal", "chelsea", 3, 1, day=1),
            _make_example("arsenal", "liverpool", 3, 2, day=2),
            # Chelsea scores 1 per game
            _make_example("chelsea", "arsenal", 1, 0, day=3),
            _make_example("chelsea", "liverpool", 1, 2, day=4),
        ]
        ext.fit(examples)
        arsenal = ext.extract("g", "arsenal", "dummy", _dt(10))
        chelsea = ext.extract("g", "chelsea", "dummy", _dt(10))
        assert arsenal.features["home_attack"] > chelsea.features["home_attack"]

    def test_leaky_defense_has_higher_defense_strength(self) -> None:
        # Higher defense value = concedes more = weaker defense.
        # To make Arsenal leaky, the HOME teams must score 3 against Arsenal (away).
        ext = SoccerFeatureExtractor()
        examples = [
            # Home teams score 3 against Arsenal (away) → Arsenal concedes 3 per game
            _make_example("chelsea", "arsenal", 3, 1, day=1),
            _make_example("liverpool", "arsenal", 3, 1, day=2),
            # Home teams score 0 against Chelsea (away) → Chelsea concedes 0 per game
            _make_example("arsenal", "chelsea", 0, 1, day=3),
            _make_example("liverpool", "chelsea", 0, 1, day=4),
        ]
        ext.fit(examples)
        arsenal = ext.extract("g", "dummy", "arsenal", _dt(10))
        chelsea = ext.extract("g", "dummy", "chelsea", _dt(10))
        # arsenal concedes more → higher away_defense value
        assert arsenal.features["away_defense"] > chelsea.features["away_defense"]

    def test_average_team_has_strength_near_one(self) -> None:
        # With perfectly average data (all teams score/concede the same), strength ≈ 1.0
        ext = SoccerFeatureExtractor()
        examples = [
            _make_example("a", "b", 2, 2, day=1),
            _make_example("b", "a", 2, 2, day=2),
        ]
        ext.fit(examples)
        result = ext.extract("g", "a", "b", _dt(10))
        assert abs(result.features["home_attack"] - 1.0) < 1e-9
        assert abs(result.features["away_attack"] - 1.0) < 1e-9
