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


class TestNFLFeatureExtractorRestDays:
    def test_rest_days_present_in_features(self) -> None:
        # Arrange
        extractor = NFLFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("g", "chiefs", "bears", _dt(7))

        # Assert
        assert "home_rest_days" in result.features
        assert "away_rest_days" in result.features

    def test_rest_days_computed_from_last_game(self) -> None:
        # Arrange — chiefs played day 1; extract on day 8 → 7 days rest
        extractor = NFLFeatureExtractor()
        extractor.fit([_make_example("chiefs", "bears", 24, 10, day=1)])

        # Act
        result = extractor.extract("g", "chiefs", "packers", _dt(8))

        # Assert
        assert abs(result.features["home_rest_days"] - 7.0) < 0.1

    def test_no_prior_game_gives_default_rest(self) -> None:
        # Arrange
        extractor = NFLFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("g", "new_team", "bears", _dt(7))

        # Assert
        assert result.features["home_rest_days"] == 7.0

    def test_away_rest_uses_away_team_history(self) -> None:
        # Arrange — bears last played as away on day 1; extract bears as away on day 8
        extractor = NFLFeatureExtractor()
        extractor.fit([_make_example("chiefs", "bears", 24, 10, day=1)])

        # Act
        result = extractor.extract("g", "packers", "bears", _dt(8))

        # Assert
        assert abs(result.features["away_rest_days"] - 7.0) < 0.1


class TestNFLFeatureExtractorRecentForm:
    def test_form_present_in_features(self) -> None:
        # Arrange
        extractor = NFLFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("g", "chiefs", "bears", _dt(7))

        # Assert
        assert "home_form_5" in result.features
        assert "away_form_5" in result.features

    def test_no_games_gives_neutral_form(self) -> None:
        # Arrange
        extractor = NFLFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("g", "chiefs", "bears", _dt(7))

        # Assert
        assert result.features["home_form_5"] == 0.5
        assert result.features["away_form_5"] == 0.5

    def test_all_wins_gives_form_one(self) -> None:
        # Arrange — chiefs win 5 games straight (as home team, days 1–5)
        extractor = NFLFeatureExtractor()
        examples = [_make_example("chiefs", "bears", 21, 14, day=i) for i in range(1, 6)]
        extractor.fit(examples)

        # Act
        result = extractor.extract("g", "chiefs", "packers", _dt(10))

        # Assert
        assert result.features["home_form_5"] == 1.0

    def test_all_losses_gives_form_zero(self) -> None:
        # Arrange — bears lose 5 games straight (as away team, days 1–5)
        extractor = NFLFeatureExtractor()
        examples = [_make_example("chiefs", "bears", 21, 14, day=i) for i in range(1, 6)]
        extractor.fit(examples)

        # Act
        result = extractor.extract("g", "packers", "bears", _dt(10))

        # Assert
        assert result.features["away_form_5"] == 0.0

    def test_form_uses_only_last_five_games(self) -> None:
        # Arrange — chiefs lose 3 early games then win 5 straight
        # Form window should only see the last 5 wins
        extractor = NFLFeatureExtractor()
        early_losses = [_make_example("bears", "chiefs", 21, 14, day=i) for i in range(1, 4)]
        recent_wins = [_make_example("chiefs", "bears", 21, 14, day=i) for i in range(4, 9)]
        extractor.fit(early_losses + recent_wins)

        # Act — extract on day 15 so all 8 games are prior
        result = extractor.extract("g", "chiefs", "packers", _dt(15))

        # Assert — last 5 are all wins
        assert result.features["home_form_5"] == 1.0


class TestNFLFeatureExtractorWeather:
    def test_weather_features_present_in_feature_set(self) -> None:
        # Arrange
        extractor = NFLFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract(
            "game-1",
            "chiefs",
            "bears",
            _dt(7),
            temperature=32.0,
            wind_mph=18.0,
            precipitation=True,
        )

        # Assert
        assert "home_temperature" in result.features
        assert "wind_mph" in result.features
        assert "is_precipitation" in result.features

    def test_no_weather_gives_neutral_defaults(self) -> None:
        # Arrange
        extractor = NFLFeatureExtractor()
        extractor.fit([])

        # Act — no weather kwargs passed
        result = extractor.extract("game-1", "chiefs", "bears", _dt(7))

        # Assert
        assert result.features["home_temperature"] == 60.0
        assert result.features["wind_mph"] == 0.0
        assert result.features["is_precipitation"] == 0.0

    def test_wind_feature_passed_through(self) -> None:
        # Arrange
        extractor = NFLFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract(
            "game-1",
            "chiefs",
            "bears",
            _dt(7),
            wind_mph=20.0,
        )

        # Assert
        assert result.features["wind_mph"] == 20.0

    def test_precipitation_feature_is_float(self) -> None:
        # Arrange
        extractor = NFLFeatureExtractor()
        extractor.fit([])

        # Act — no precipitation (default)
        result_no_precip = extractor.extract("game-1", "chiefs", "bears", _dt(7))
        # Act — precipitation present
        result_precip = extractor.extract(
            "game-2",
            "chiefs",
            "bears",
            _dt(7),
            precipitation=True,
        )

        # Assert — is_precipitation is always a float, never a bool
        assert isinstance(result_no_precip.features["is_precipitation"], float)
        assert isinstance(result_precip.features["is_precipitation"], float)
        assert result_no_precip.features["is_precipitation"] == 0.0
        assert result_precip.features["is_precipitation"] == 1.0
