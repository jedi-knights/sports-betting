"""Flat unit bet sizer."""

from __future__ import annotations

from .types import BetSizing


class FlatUnitSizer:
    """Sizes every bet at a fixed unit stake regardless of edge or odds.

    Args:
        unit: Fixed stake amount per bet.
    """

    def __init__(self, unit: float) -> None:
        self._unit = unit

    def size(self, edge: float, decimal_odds: float, bankroll: float) -> BetSizing:
        """Return the configured unit stake.

        Args:
            edge: Ignored — flat sizing does not vary with edge.
            decimal_odds: Ignored — flat sizing does not vary with odds.
            bankroll: Used only to compute the ``fraction`` field.

        Returns:
            BetSizing with a constant stake equal to the configured unit.
        """
        fraction = self._unit / bankroll if bankroll > 0.0 else 0.0
        return BetSizing(stake=self._unit, fraction=fraction, bankroll=bankroll)
