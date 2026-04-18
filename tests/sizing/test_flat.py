"""Tests for flat unit bet sizer."""

from __future__ import annotations

from bet.sizing.flat import FlatUnitSizer
from bet.sizing.protocols import Sizer
from bet.sizing.types import BetSizing


class TestFlatUnitSizer:
    def test_returns_bet_sizing(self) -> None:
        sizer = FlatUnitSizer(unit=50.0)
        result = sizer.size(edge=0.10, decimal_odds=2.0, bankroll=1000.0)
        assert isinstance(result, BetSizing)

    def test_stake_equals_unit(self) -> None:
        sizer = FlatUnitSizer(unit=50.0)
        result = sizer.size(edge=0.10, decimal_odds=2.0, bankroll=1000.0)
        assert result.stake == 50.0

    def test_stake_ignores_edge(self) -> None:
        sizer = FlatUnitSizer(unit=50.0)
        low = sizer.size(edge=0.02, decimal_odds=2.0, bankroll=1000.0)
        high = sizer.size(edge=0.50, decimal_odds=2.0, bankroll=1000.0)
        assert low.stake == high.stake == 50.0

    def test_stake_ignores_odds(self) -> None:
        sizer = FlatUnitSizer(unit=50.0)
        low_odds = sizer.size(edge=0.10, decimal_odds=1.5, bankroll=1000.0)
        high_odds = sizer.size(edge=0.10, decimal_odds=5.0, bankroll=1000.0)
        assert low_odds.stake == high_odds.stake == 50.0

    def test_fraction_is_unit_over_bankroll(self) -> None:
        sizer = FlatUnitSizer(unit=50.0)
        result = sizer.size(edge=0.10, decimal_odds=2.0, bankroll=1000.0)
        assert abs(result.fraction - 0.05) < 1e-9

    def test_bankroll_field_preserved(self) -> None:
        sizer = FlatUnitSizer(unit=50.0)
        result = sizer.size(edge=0.10, decimal_odds=2.0, bankroll=1000.0)
        assert result.bankroll == 1000.0

    def test_zero_edge_still_returns_unit_stake(self) -> None:
        sizer = FlatUnitSizer(unit=50.0)
        result = sizer.size(edge=0.0, decimal_odds=2.0, bankroll=1000.0)
        assert result.stake == 50.0

    def test_negative_edge_still_returns_unit_stake(self) -> None:
        sizer = FlatUnitSizer(unit=50.0)
        result = sizer.size(edge=-0.10, decimal_odds=2.0, bankroll=1000.0)
        assert result.stake == 50.0

    def test_zero_bankroll_fraction_is_zero(self) -> None:
        sizer = FlatUnitSizer(unit=50.0)
        result = sizer.size(edge=0.10, decimal_odds=2.0, bankroll=0.0)
        assert result.fraction == 0.0

    def test_implements_sizer_protocol(self) -> None:
        assert isinstance(FlatUnitSizer(unit=10.0), Sizer)
