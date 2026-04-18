"""Domain types for the Bankroll Management context."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BetSizing:
    """Computed stake recommendation for a single bet.

    Attributes:
        stake: Absolute amount to wager.
        fraction: Proportion of bankroll staked.
        bankroll: Bankroll at the time of sizing.
    """

    stake: float
    fraction: float
    bankroll: float


@dataclass
class KellyFraction:
    """Kelly Criterion fractions computed for a given edge and odds.

    Attributes:
        full_kelly: f* = max(0, edge / (decimal_odds − 1)).
        half_kelly: f* / 2.
        quarter_kelly: f* / 4.
        edge: EV per unit staked used in the computation.
        decimal_odds: Decimal odds used in the computation.
    """

    full_kelly: float
    half_kelly: float
    quarter_kelly: float
    edge: float
    decimal_odds: float
