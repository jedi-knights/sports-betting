"""Tests for the MLB Elo feature extractor."""

from __future__ import annotations

from datetime import UTC, datetime

from bet.features.mlb import MLBFeatureExtractor
from bet.modeling.types import ActualOutcome, FeatureSet, TrainingExample


def _dt(day: int) -> datetime:
    return datetime(2024, 4, day, tzinfo=UTC)


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
            sport="mlb",
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


class TestMLBFeatureExtractorBasics:
    def test_extract_returns_feature_set(self) -> None:
        # Arrange
        extractor = MLBFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "yankees", "redsox", _dt(10))

        # Assert
        assert isinstance(result, FeatureSet)

    def test_sport_is_mlb(self) -> None:
        # Arrange
        extractor = MLBFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "yankees", "redsox", _dt(10))

        # Assert
        assert result.sport == "mlb"

    def test_extract_includes_elo_features(self) -> None:
        # Arrange
        extractor = MLBFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "yankees", "redsox", _dt(10))

        # Assert
        for key in ("home_elo", "away_elo", "elo_diff"):
            assert key in result.features

    def test_extract_includes_rest_and_form(self) -> None:
        # Arrange
        extractor = MLBFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "yankees", "redsox", _dt(10))

        # Assert
        for key in ("home_rest_days", "away_rest_days", "home_form_5", "away_form_5"):
            assert key in result.features

    def test_no_weather_features(self) -> None:
        # Arrange
        extractor = MLBFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "yankees", "redsox", _dt(10))

        # Assert — weather handled at pipeline level, not embedded in features
        assert "wind_mph" not in result.features
        assert "is_precipitation" not in result.features

    def test_unknown_teams_start_at_initial_rating(self) -> None:
        # Arrange
        extractor = MLBFeatureExtractor(initial_rating=1500.0)
        extractor.fit([])

        # Act
        result = extractor.extract("game-1", "yankees", "redsox", _dt(10))

        # Assert
        assert result.features["home_elo"] == 1500.0
        assert result.features["away_elo"] == 1500.0

    def test_default_rest_days_when_no_prior_games(self) -> None:
        # Arrange — no history; MLB default rest is 1 day (daily schedule)
        extractor = MLBFeatureExtractor()
        extractor.fit([])

        # Act
        result = extractor.extract("pred", "yankees", "redsox", _dt(10))

        # Assert
        assert result.features["home_rest_days"] == 1.0
        assert result.features["away_rest_days"] == 1.0

    def test_winning_team_gains_elo(self) -> None:
        # Arrange
        extractor = MLBFeatureExtractor(initial_rating=1500.0)
        extractor.fit([_make_example("yankees", "redsox", 5, 2, 1)])

        # Act
        result = extractor.extract("pred", "yankees", "redsox", _dt(5))

        # Assert
        assert result.features["home_elo"] > 1500.0
        assert result.features["away_elo"] < 1500.0

    def test_lookahead_guard_excludes_future_games(self) -> None:
        # Arrange
        extractor = MLBFeatureExtractor()
        past = _make_example("yankees", "redsox", 5, 2, 1)
        future = _make_example("yankees", "orioles", 3, 4, 20)
        extractor.fit([past, future])

        # Act
        result = extractor.extract("pred", "yankees", "redsox", _dt(10))

        # Assert
        baseline = MLBFeatureExtractor()
        baseline.fit([past])
        baseline_result = baseline.extract("pred", "yankees", "redsox", _dt(10))
        assert result.features["home_elo"] == baseline_result.features["home_elo"]
