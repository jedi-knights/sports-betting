"""Tests for _build_model_and_extractor in the CLI."""

from __future__ import annotations

import pytest

from bet.cli import _build_model_and_extractor

_SOCCER_LEAGUES = [
    "epl",
    "mls",
    "nwsl",
    "usl_super_league",
    "usl_w_league",
    "wpsl",
    "ecnl",
    "ecrl",
]


class TestBuildModelAndExtractor:
    def test_poisson_model_raises_for_non_soccer_sport(self) -> None:
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="poisson"):
            _build_model_and_extractor("nfl", "poisson", 20.0, True)

    @pytest.mark.parametrize("sport", _SOCCER_LEAGUES)
    def test_poisson_model_valid_for_all_soccer_leagues(self, sport: str) -> None:
        # Arrange / Act
        from bet.modeling.poisson import PoissonModel

        model, extractor = _build_model_and_extractor(sport, "poisson", 20.0, True)

        # Assert
        assert isinstance(model, PoissonModel)

    def test_elo_model_valid_for_nfl(self) -> None:
        # Arrange / Act
        from bet.modeling.elo import EloModel

        model, extractor = _build_model_and_extractor("nfl", "elo", 20.0, True)

        # Assert
        assert isinstance(model, EloModel)
