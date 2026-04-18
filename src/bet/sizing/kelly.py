"""Kelly Criterion bet sizer."""

from __future__ import annotations

from .types import BetSizing, KellyFraction


def full_kelly(edge: float, decimal_odds: float) -> float:
    """Compute the full Kelly fraction.

    f* = max(0, edge / (decimal_odds − 1))

    Args:
        edge: EV per unit staked = model_prob × decimal_odds − 1.
        decimal_odds: Offered decimal odds (must be > 1.0 to be meaningful).

    Returns:
        Optimal bankroll fraction to wager. 0.0 when edge ≤ 0 or odds ≤ 1.
    """
    if decimal_odds <= 1.0:
        return 0.0
    return max(0.0, edge / (decimal_odds - 1.0))


def compute_kelly_fraction(edge: float, decimal_odds: float) -> KellyFraction:
    """Return all three Kelly variants for the given edge and odds.

    Args:
        edge: EV per unit staked.
        decimal_odds: Offered decimal odds.

    Returns:
        KellyFraction with full, half, and quarter Kelly values.
    """
    f = full_kelly(edge, decimal_odds)
    return KellyFraction(
        full_kelly=f,
        half_kelly=f / 2.0,
        quarter_kelly=f / 4.0,
        edge=edge,
        decimal_odds=decimal_odds,
    )


class KellySizer:
    """Sizes bets using a configurable fraction of the Kelly Criterion.

    Args:
        fraction: Multiplier applied to full Kelly. 1.0 = full Kelly,
            0.5 = half Kelly, 0.25 = quarter Kelly. Defaults to 1.0.
    """

    def __init__(self, fraction: float = 1.0) -> None:
        self._fraction = fraction

    def size(self, edge: float, decimal_odds: float, bankroll: float) -> BetSizing:
        """Compute Kelly-sized stake.

        Args:
            edge: EV per unit staked.
            decimal_odds: Offered decimal odds.
            bankroll: Current bankroll.

        Returns:
            BetSizing with Kelly-derived stake, never negative.
        """
        f = full_kelly(edge, decimal_odds) * self._fraction
        return BetSizing(stake=bankroll * f, fraction=f, bankroll=bankroll)
