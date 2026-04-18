"""Tests for the expected value calculation."""

from __future__ import annotations

import pytest

from bet.value.ev import expected_value


class TestExpectedValue:
    def test_positive_when_model_prob_exceeds_breakeven(self) -> None:
        # 0.55 × 2.10 − 1 = 0.155
        assert abs(expected_value(0.55, 2.10) - 0.155) < 1e-9

    def test_negative_when_model_prob_below_breakeven(self) -> None:
        # 0.40 × 2.10 − 1 = −0.16
        assert abs(expected_value(0.40, 2.10) - (-0.16)) < 1e-9

    def test_zero_at_exact_breakeven(self) -> None:
        # model_prob = 1/decimal_odds → EV = 0
        decimal_odds = 2.10
        assert abs(expected_value(1.0 / decimal_odds, decimal_odds)) < 1e-9

    def test_large_edge_on_high_odds(self) -> None:
        # 0.20 × 6.0 − 1 = 0.20
        assert abs(expected_value(0.20, 6.0) - 0.20) < 1e-9

    def test_even_odds_at_fifty_percent_is_zero(self) -> None:
        # 0.50 × 2.0 − 1 = 0.0
        assert abs(expected_value(0.50, 2.0)) < 1e-9

    def test_result_type_is_float(self) -> None:
        assert isinstance(expected_value(0.55, 2.10), float)

    @pytest.mark.parametrize("prob,odds", [(0.0, 2.0), (1.0, 2.0)])
    def test_boundary_probabilities_do_not_raise(self, prob: float, odds: float) -> None:
        expected_value(prob, odds)  # should not raise
