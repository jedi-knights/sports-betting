"""Tests for _build_model_and_extractor's sport/model compatibility guards.

Elo hardcodes ``features["home_elo"]`` / ``features["away_elo"]`` in its
predict() step. The soccer feature extractors provide attack/defense
strengths instead — they don't produce Elo features. Wiring Elo to a
soccer extractor causes a silent KeyError at predict time (previously
swallowed by the pipeline's debug log), which manifests as "call
fit_calibrator() before predict()" downstream because the calibration
accumulation loop drops every fold.

These tests lock in the compatibility guard: incompatible combinations
must be rejected at build time with a clear ValueError.
"""

from __future__ import annotations

import pytest

from bet.cli import _build_model_and_extractor


class TestBuildModelAndExtractor:
    def test_elo_rejects_mls(self) -> None:
        # Act / Assert
        with pytest.raises(ValueError, match="elo"):
            _build_model_and_extractor("mls", "elo", 20.0, True)

    def test_elo_rejects_nwsl(self) -> None:
        # Act / Assert
        with pytest.raises(ValueError, match="elo"):
            _build_model_and_extractor("nwsl", "elo", 20.0, True)

    def test_elo_rejects_ecnl(self) -> None:
        # Act / Assert
        with pytest.raises(ValueError, match="elo"):
            _build_model_and_extractor("ecnl", "elo", 20.0, True)

    def test_elo_accepts_nfl(self) -> None:
        # Act
        model, extractor = _build_model_and_extractor("nfl", "elo", 20.0, True)

        # Assert
        assert model is not None
        assert extractor is not None

    def test_ensemble_rejects_soccer_because_it_contains_elo(self) -> None:
        # Act / Assert
        with pytest.raises(ValueError, match="ensemble"):
            _build_model_and_extractor("mls", "ensemble", 20.0, True)

    def test_ensemble_accepts_nba(self) -> None:
        # Act
        model, extractor = _build_model_and_extractor("nba", "ensemble", 20.0, True)

        # Assert
        assert model is not None
        assert extractor is not None

    def test_poisson_accepts_mls(self) -> None:
        # Act
        model, extractor = _build_model_and_extractor("mls", "poisson", 20.0, True)

        # Assert
        assert model is not None
        assert extractor is not None

    def test_poisson_rejects_nfl(self) -> None:
        # Act / Assert — poisson has always been rejected for non-soccer
        with pytest.raises(ValueError):
            _build_model_and_extractor("nfl", "poisson", 20.0, True)

    def test_logistic_accepts_mls(self) -> None:
        # Act — feature-agnostic, works everywhere
        model, extractor = _build_model_and_extractor("mls", "logistic", 20.0, True)

        # Assert
        assert model is not None
        assert extractor is not None
