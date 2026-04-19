"""Parametrized tests for all soccer league feature extractors.

Each league extractor uses the same Poisson attack/defense algorithm but
returns a league-specific sport slug in the extracted FeatureSet.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bet.features.ecnl import ECNLFeatureExtractor
from bet.features.ecrl import ECRLFeatureExtractor
from bet.features.epl import EPLFeatureExtractor
from bet.features.mls import MLSFeatureExtractor
from bet.features.nwsl import NWSLFeatureExtractor
from bet.features.usl_super_league import USLSuperLeagueFeatureExtractor
from bet.features.usl_w_league import USLWLeagueFeatureExtractor
from bet.features.wpsl import WPSLFeatureExtractor
from bet.modeling.types import FeatureSet


def _dt(day: int) -> datetime:
    return datetime(2024, 1, day, tzinfo=UTC)


@pytest.mark.parametrize(
    "extractor_cls, expected_sport",
    [
        (EPLFeatureExtractor, "epl"),
        (MLSFeatureExtractor, "mls"),
        (NWSLFeatureExtractor, "nwsl"),
        (USLSuperLeagueFeatureExtractor, "usl_super_league"),
        (USLWLeagueFeatureExtractor, "usl_w_league"),
        (WPSLFeatureExtractor, "wpsl"),
        (ECNLFeatureExtractor, "ecnl"),
        (ECRLFeatureExtractor, "ecrl"),
    ],
)
class TestSoccerLeagueExtractor:
    def test_returns_feature_set(self, extractor_cls, expected_sport) -> None:
        # Arrange
        ext = extractor_cls()
        ext.fit([])

        # Act
        result = ext.extract("g", "team_a", "team_b", _dt(10))

        # Assert
        assert isinstance(result, FeatureSet)

    def test_sport_slug_is_correct(self, extractor_cls, expected_sport) -> None:
        # Arrange
        ext = extractor_cls()
        ext.fit([])

        # Act
        result = ext.extract("g", "team_a", "team_b", _dt(10))

        # Assert
        assert result.sport == expected_sport

    def test_returns_four_strength_features(self, extractor_cls, expected_sport) -> None:
        # Arrange
        ext = extractor_cls()
        ext.fit([])

        # Act
        result = ext.extract("g", "team_a", "team_b", _dt(10))

        # Assert
        for key in ("home_attack", "home_defense", "away_attack", "away_defense"):
            assert key in result.features, f"missing feature: {key}"

    def test_unknown_teams_default_to_one(self, extractor_cls, expected_sport) -> None:
        # Arrange
        ext = extractor_cls()
        ext.fit([])

        # Act
        result = ext.extract("g", "unknown_a", "unknown_b", _dt(10))

        # Assert
        for key in ("home_attack", "home_defense", "away_attack", "away_defense"):
            assert result.features[key] == 1.0, f"{key} should default to 1.0"
