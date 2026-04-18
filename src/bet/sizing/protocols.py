"""Protocol for the Bankroll Management context."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .types import BetSizing


@runtime_checkable
class Sizer(Protocol):
    """Computes a stake size given edge, odds, and current bankroll."""

    def size(self, edge: float, decimal_odds: float, bankroll: float) -> BetSizing:
        """Compute the recommended stake for a single bet.

        Args:
            edge: EV per unit staked = model_prob × decimal_odds − 1.
            decimal_odds: Offered decimal odds.
            bankroll: Current bankroll.

        Returns:
            BetSizing with stake, fraction, and bankroll context.
        """
        ...
