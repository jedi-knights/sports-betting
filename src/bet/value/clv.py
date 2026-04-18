"""Closing line value computation."""

from __future__ import annotations

from .types import CLVResult, ValueBet


def compute_clv(value_bet: ValueBet, closing_decimal_odds: float) -> CLVResult:
    """Compute closing line value for a placed bet.

    CLV = closing_implied_probability − bet_implied_probability

    Positive CLV means the bet obtained better odds than the closing line.
    The closing line is the most efficient price available — consistently
    beating it is the standard evidence of genuine predictive edge,
    independent of short-run win/loss outcomes.

    Args:
        value_bet: The bet whose CLV is being measured.
        closing_decimal_odds: Final decimal odds posted before game time.

    Returns:
        A CLVResult with the closing probability and CLV delta.
    """
    closing_prob = 1.0 / closing_decimal_odds
    bet_implied_prob = 1.0 / value_bet.decimal_odds
    return CLVResult(
        value_bet=value_bet,
        closing_decimal_odds=closing_decimal_odds,
        closing_prob=closing_prob,
        clv=closing_prob - bet_implied_prob,
    )
