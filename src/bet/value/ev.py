"""Expected value calculation for sports betting."""

from __future__ import annotations


def expected_value(model_prob: float, decimal_odds: float) -> float:
    """Compute expected value per unit staked.

    EV = model_prob × decimal_odds − 1

    Positive EV indicates a value bet — the model believes the outcome is
    more likely than the odds imply. A value of 0.05 means 5 cents expected
    profit per dollar wagered over the long run.

    Args:
        model_prob: Calibrated model probability for the outcome in [0, 1].
        decimal_odds: Offered decimal odds (e.g. 2.10 pays £2.10 per £1 staked).

    Returns:
        Expected value per unit. Positive = value bet. Negative = losing bet.
    """
    return model_prob * decimal_odds - 1.0
