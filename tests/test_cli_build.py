"""Tests for _build_model_and_extractor in the CLI."""

from __future__ import annotations

import pytest

from bet.cli import _build_model_and_extractor


class TestBuildModelAndExtractor:
    def test_poisson_model_raises_for_non_soccer_sport(self) -> None:
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="poisson"):
            _build_model_and_extractor("nfl", "poisson", 20.0, True)

    def test_poisson_model_valid_for_soccer(self) -> None:
        # Arrange / Act
        from bet.modeling.poisson import PoissonModel

        model, extractor = _build_model_and_extractor("soccer", "poisson", 20.0, True)

        # Assert
        assert isinstance(model, PoissonModel)

    def test_elo_model_valid_for_nfl(self) -> None:
        # Arrange / Act
        from bet.modeling.elo import EloModel

        model, extractor = _build_model_and_extractor("nfl", "elo", 20.0, True)

        # Assert
        assert isinstance(model, EloModel)
