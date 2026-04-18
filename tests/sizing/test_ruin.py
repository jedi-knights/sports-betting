"""Tests for ruin probability estimator."""

from __future__ import annotations

from bet.sizing.ruin import estimate_ruin_probability


class TestEstimateRuinProbability:
    def test_returns_float(self) -> None:
        result = estimate_ruin_probability(
            edge=0.05,
            decimal_odds=2.0,
            kelly_fraction=0.25,
            initial_bankroll=1000.0,
            seed=42,
        )
        assert isinstance(result, float)

    def test_result_in_unit_interval(self) -> None:
        result = estimate_ruin_probability(
            edge=0.05,
            decimal_odds=2.0,
            kelly_fraction=0.25,
            initial_bankroll=1000.0,
            seed=42,
        )
        assert 0.0 <= result <= 1.0

    def test_zero_edge_yields_zero_ruin(self) -> None:
        # kelly_f = 0 → no bets placed → bankroll never moves → ruin prob = 0
        result = estimate_ruin_probability(
            edge=0.0,
            decimal_odds=2.0,
            kelly_fraction=0.25,
            initial_bankroll=1000.0,
            seed=42,
        )
        assert result == 0.0

    def test_negative_edge_yields_zero_ruin(self) -> None:
        # full Kelly clamped to 0 for negative edge → no bets placed
        result = estimate_ruin_probability(
            edge=-0.10,
            decimal_odds=2.0,
            kelly_fraction=0.25,
            initial_bankroll=1000.0,
            seed=42,
        )
        assert result == 0.0

    def test_deterministic_with_seed(self) -> None:
        kwargs: dict = {
            "edge": 0.05,
            "decimal_odds": 2.0,
            "kelly_fraction": 0.25,
            "initial_bankroll": 1000.0,
            "n_simulations": 500,
            "seed": 42,
        }
        r1 = estimate_ruin_probability(**kwargs)
        r2 = estimate_ruin_probability(**kwargs)
        assert r1 == r2

    def test_very_high_edge_gives_low_ruin(self) -> None:
        # 50% EV at quarter Kelly over 200 bets should almost never ruin
        result = estimate_ruin_probability(
            edge=0.50,
            decimal_odds=2.0,
            kelly_fraction=0.25,
            initial_bankroll=1000.0,
            n_bets=200,
            n_simulations=2000,
            seed=99,
        )
        assert result < 0.10

    def test_ruin_threshold_kwarg_accepted(self) -> None:
        result = estimate_ruin_probability(
            edge=0.05,
            decimal_odds=2.0,
            kelly_fraction=0.25,
            initial_bankroll=1000.0,
            ruin_threshold=0.5,
            seed=42,
        )
        assert 0.0 <= result <= 1.0
