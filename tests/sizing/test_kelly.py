"""Tests for Kelly Criterion bet sizer."""

from __future__ import annotations

from bet.sizing.kelly import KellySizer, compute_kelly_fraction, full_kelly
from bet.sizing.protocols import Sizer
from bet.sizing.types import BetSizing, KellyFraction


class TestFullKelly:
    def test_positive_edge_formula(self) -> None:
        # f* = 0.10 / (2.0 - 1) = 0.10
        assert abs(full_kelly(0.10, 2.0) - 0.10) < 1e-9

    def test_high_odds(self) -> None:
        # f* = 0.05 / (1.5 - 1) = 0.10
        assert abs(full_kelly(0.05, 1.5) - 0.10) < 1e-9

    def test_zero_edge_returns_zero(self) -> None:
        assert full_kelly(0.0, 2.0) == 0.0

    def test_negative_edge_clamped_to_zero(self) -> None:
        assert full_kelly(-0.10, 2.0) == 0.0

    def test_odds_at_or_below_one_returns_zero(self) -> None:
        assert full_kelly(0.10, 1.0) == 0.0
        assert full_kelly(0.10, 0.5) == 0.0


class TestComputeKellyFraction:
    def test_returns_kelly_fraction(self) -> None:
        result = compute_kelly_fraction(0.10, 2.0)
        assert isinstance(result, KellyFraction)

    def test_full_kelly_field(self) -> None:
        result = compute_kelly_fraction(0.10, 2.0)
        assert abs(result.full_kelly - 0.10) < 1e-9

    def test_half_kelly_is_half_of_full(self) -> None:
        result = compute_kelly_fraction(0.10, 2.0)
        assert abs(result.half_kelly - result.full_kelly / 2) < 1e-9

    def test_quarter_kelly_is_quarter_of_full(self) -> None:
        result = compute_kelly_fraction(0.10, 2.0)
        assert abs(result.quarter_kelly - result.full_kelly / 4) < 1e-9

    def test_edge_and_odds_preserved(self) -> None:
        result = compute_kelly_fraction(0.10, 2.0)
        assert result.edge == 0.10
        assert result.decimal_odds == 2.0

    def test_zero_edge_all_fractions_zero(self) -> None:
        result = compute_kelly_fraction(0.0, 2.0)
        assert result.full_kelly == 0.0
        assert result.half_kelly == 0.0
        assert result.quarter_kelly == 0.0


class TestKellySizerFullKelly:
    def test_returns_bet_sizing(self) -> None:
        sizer = KellySizer(fraction=1.0)
        result = sizer.size(edge=0.10, decimal_odds=2.0, bankroll=1000.0)
        assert isinstance(result, BetSizing)

    def test_stake_formula(self) -> None:
        # kelly_f = 0.10 / (2.0 - 1) = 0.10; stake = 1000 × 0.10 = 100
        sizer = KellySizer(fraction=1.0)
        result = sizer.size(edge=0.10, decimal_odds=2.0, bankroll=1000.0)
        assert abs(result.stake - 100.0) < 1e-9

    def test_fraction_field(self) -> None:
        sizer = KellySizer(fraction=1.0)
        result = sizer.size(edge=0.10, decimal_odds=2.0, bankroll=1000.0)
        assert abs(result.fraction - 0.10) < 1e-9

    def test_bankroll_field_preserved(self) -> None:
        sizer = KellySizer(fraction=1.0)
        result = sizer.size(edge=0.10, decimal_odds=2.0, bankroll=1000.0)
        assert result.bankroll == 1000.0

    def test_zero_edge_returns_zero_stake(self) -> None:
        sizer = KellySizer(fraction=1.0)
        result = sizer.size(edge=0.0, decimal_odds=2.0, bankroll=1000.0)
        assert result.stake == 0.0
        assert result.fraction == 0.0

    def test_negative_edge_returns_zero_stake(self) -> None:
        sizer = KellySizer(fraction=1.0)
        result = sizer.size(edge=-0.10, decimal_odds=2.0, bankroll=1000.0)
        assert result.stake == 0.0
        assert result.fraction == 0.0

    def test_implements_sizer_protocol(self) -> None:
        assert isinstance(KellySizer(), Sizer)


class TestKellySizerHalfKelly:
    def test_stake_is_half_of_full_kelly(self) -> None:
        full = KellySizer(fraction=1.0).size(
            edge=0.10, decimal_odds=2.0, bankroll=1000.0
        )
        half = KellySizer(fraction=0.5).size(
            edge=0.10, decimal_odds=2.0, bankroll=1000.0
        )
        assert abs(half.stake - full.stake / 2) < 1e-9

    def test_fraction_field_adjusted(self) -> None:
        result = KellySizer(fraction=0.5).size(
            edge=0.10, decimal_odds=2.0, bankroll=1000.0
        )
        assert abs(result.fraction - 0.05) < 1e-9


class TestKellySizerQuarterKelly:
    def test_stake_is_quarter_of_full_kelly(self) -> None:
        full = KellySizer(fraction=1.0).size(
            edge=0.10, decimal_odds=2.0, bankroll=1000.0
        )
        quarter = KellySizer(fraction=0.25).size(
            edge=0.10, decimal_odds=2.0, bankroll=1000.0
        )
        assert abs(quarter.stake - full.stake / 4) < 1e-9

    def test_fraction_field_adjusted(self) -> None:
        result = KellySizer(fraction=0.25).size(
            edge=0.10, decimal_odds=2.0, bankroll=1000.0
        )
        assert abs(result.fraction - 0.025) < 1e-9
