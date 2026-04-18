"""Tests for the NBA Elo feature extractor."""

from __future__ import annotations

from datetime import UTC, datetime

from bet.features.nba import NBAFeatureExtractor
from bet.modeling.types import ActualOutcome, FeatureSet, TrainingExample


def _dt(day: int) -> datetime:
    return datetime(2024, 1, day, tzinfo=UTC)


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
            sport="nba",
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


class TestNBAFeatureExtractorBasics:
    def test_extract_returns_feature_set(self) -> None:
        # Arrange
        extractor = NBAFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "lakers", "celtics", _dt(7))

        # Assert
        assert isinstance(result, FeatureSet)

    def test_sport_is_nba(self) -> None:
        # Arrange
        extractor = NBAFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "lakers", "celtics", _dt(7))

        # Assert
        assert result.sport == "nba"

    def test_extract_includes_elo_features(self) -> None:
        # Arrange
        extractor = NBAFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "lakers", "celtics", _dt(7))

        # Assert
        for key in ("home_elo", "away_elo", "elo_diff"):
            assert key in result.features

    def test_extract_includes_rest_and_form(self) -> None:
        # Arrange
        extractor = NBAFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "lakers", "celtics", _dt(7))

        # Assert
        for key in ("home_rest_days", "away_rest_days", "home_form_5", "away_form_5"):
            assert key in result.features

    def test_no_weather_features(self) -> None:
        # Arrange
        extractor = NBAFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "lakers", "celtics", _dt(7))

        # Assert — NBA is an indoor sport; no weather features
        assert "home_temperature" not in result.features
        assert "wind_mph" not in result.features
        assert "is_precipitation" not in result.features

    def test_unknown_teams_start_at_initial_rating(self) -> None:
        # Arrange
        extractor = NBAFeatureExtractor(initial_rating=1500.0)
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "lakers", "celtics", _dt(7))

        # Assert
        assert result.features["home_elo"] == 1500.0
        assert result.features["away_elo"] == 1500.0
        assert result.features["elo_diff"] == 0.0

    def test_lookahead_guard_excludes_future_games(self) -> None:
        # Arrange — two games; one is on day 10 (future relative to prediction)
        extractor = NBAFeatureExtractor()
        past = _make_example("lakers", "celtics", 110, 100, 1)
        future = _make_example("lakers", "warriors", 115, 105, 10)
        extractor.fit([past, future])

        # Act — predict as of day 5 (between the two games)
        result = extractor.extract("pred", "lakers", "celtics", _dt(5))

        # Assert — only the day-1 game should affect lakers' elo; future game excluded
        baseline = NBAFeatureExtractor()
        baseline.fit([past])
        baseline_result = baseline.extract("pred", "lakers", "celtics", _dt(5))
        assert result.features["home_elo"] == baseline_result.features["home_elo"]

    def test_winning_team_gains_elo(self) -> None:
        # Arrange
        extractor = NBAFeatureExtractor(initial_rating=1500.0)
        extractor.fit([_make_example("lakers", "celtics", 115, 100, 1)])

        # Act
        result = extractor.extract("pred", "lakers", "celtics", _dt(5))

        # Assert — lakers won so their Elo should be above baseline 1500
        assert result.features["home_elo"] > 1500.0
        assert result.features["away_elo"] < 1500.0

    def test_default_rest_days_when_no_prior_games(self) -> None:
        # Arrange — no history
        extractor = NBAFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("pred", "lakers", "celtics", _dt(10))

        # Assert — default rest days should be used (NBA default is 2.0)
        assert result.features["home_rest_days"] == 2.0
        assert result.features["away_rest_days"] == 2.0

    def test_form_defaults_to_half_when_no_history(self) -> None:
        # Arrange
        extractor = NBAFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("pred", "lakers", "celtics", _dt(10))

        # Assert — 0.5 indicates no information (neither good nor bad form)
        assert result.features["home_form_5"] == 0.5
        assert result.features["away_form_5"] == 0.5
