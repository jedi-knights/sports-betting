"""Tests for closing line value computation."""

from __future__ import annotations

from datetime import UTC, datetime

from bet.value.clv import compute_clv
from bet.value.types import CLVResult, ValueBet


def _make_value_bet(decimal_odds: float = 2.20) -> ValueBet:
    return ValueBet(
        event_id="game-1",
        market_id="m1",
        side="home_win",
        model_prob=0.55,
        market_prob=1.0 / decimal_odds,
        decimal_odds=decimal_odds,
        edge=0.55 * decimal_odds - 1.0,
        detected_at=datetime(2023, 10, 1, tzinfo=UTC),
    )


class TestComputeCLV:
    def test_positive_clv_when_closing_odds_shorter(self) -> None:
        # Bet at 2.20, closes at 2.05 → closing_prob > bet_implied → CLV > 0
        result = compute_clv(_make_value_bet(2.20), closing_decimal_odds=2.05)
        assert result.clv > 0.0

    def test_negative_clv_when_closing_odds_longer(self) -> None:
        # Bet at 2.20, closes at 2.35 → closing_prob < bet_implied → CLV < 0
        result = compute_clv(_make_value_bet(2.20), closing_decimal_odds=2.35)
        assert result.clv < 0.0

    def test_zero_clv_when_odds_unchanged(self) -> None:
        result = compute_clv(_make_value_bet(2.20), closing_decimal_odds=2.20)
        assert abs(result.clv) < 1e-9

    def test_closing_prob_is_one_over_closing_odds(self) -> None:
        result = compute_clv(_make_value_bet(2.00), closing_decimal_odds=2.00)
        assert abs(result.closing_prob - 0.5) < 1e-9

    def test_result_contains_original_value_bet(self) -> None:
        vb = _make_value_bet(2.20)
        result = compute_clv(vb, closing_decimal_odds=2.05)
        assert result.value_bet == vb

    def test_clv_formula_matches_definition(self) -> None:
        # CLV = closing_prob − bet_implied_prob
        decimal_odds = 2.20
        closing_odds = 2.05
        result = compute_clv(_make_value_bet(decimal_odds), closing_odds)
        expected_clv = 1.0 / closing_odds - 1.0 / decimal_odds
        assert abs(result.clv - expected_clv) < 1e-9

    def test_returns_clv_result(self) -> None:
        result = compute_clv(_make_value_bet(), closing_decimal_odds=2.10)
        assert isinstance(result, CLVResult)

    def test_closing_decimal_odds_stored_on_result(self) -> None:
        result = compute_clv(_make_value_bet(2.20), closing_decimal_odds=2.05)
        assert result.closing_decimal_odds == 2.05
