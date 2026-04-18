"""Ruin probability estimator via Monte Carlo simulation."""

from __future__ import annotations

import random


def estimate_ruin_probability(
    edge: float,
    decimal_odds: float,
    kelly_fraction: float,
    initial_bankroll: float,
    n_bets: int = 1000,
    n_simulations: int = 10_000,
    ruin_threshold: float = 0.1,
    seed: int | None = None,
) -> float:
    """Estimate ruin probability via Monte Carlo simulation.

    Simulates ``n_simulations`` independent betting paths each of ``n_bets``
    bets. At every step the fractional-Kelly stake is applied to the current
    bankroll. Ruin is declared when the bankroll drops below
    ``ruin_threshold × initial_bankroll``.

    Args:
        edge: EV per unit staked = model_prob × decimal_odds − 1.
        decimal_odds: Offered decimal odds.
        kelly_fraction: Multiplier applied to full Kelly (e.g. 0.25 for
            quarter Kelly). The raw f* is computed internally.
        initial_bankroll: Starting bankroll for each simulated path.
        n_bets: Number of bets per simulated path.
        n_simulations: Number of independent paths to simulate.
        ruin_threshold: Fraction of ``initial_bankroll`` below which the
            bettor is declared ruined. Defaults to 0.1 (10%).
        seed: Random seed for reproducibility. ``None`` uses system entropy.

    Returns:
        Estimated probability of ruin in [0.0, 1.0].
    """
    raw_f = max(0.0, edge / (decimal_odds - 1.0)) if decimal_odds > 1.0 else 0.0
    f = raw_f * kelly_fraction

    if f <= 0.0:
        return 0.0

    rng = random.Random(seed)
    win_prob = (edge + 1.0) / decimal_odds
    ruin_floor = initial_bankroll * ruin_threshold
    win_mult = 1.0 + f * (decimal_odds - 1.0)
    lose_mult = 1.0 - f

    ruin_count = 0
    for _ in range(n_simulations):
        bankroll = initial_bankroll
        for _ in range(n_bets):
            if rng.random() < win_prob:
                bankroll *= win_mult
            else:
                bankroll *= lose_mult
            if bankroll < ruin_floor:
                ruin_count += 1
                break

    return ruin_count / n_simulations
