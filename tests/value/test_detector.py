"""Tests for the minimum-edge ValueDetector."""

from __future__ import annotations

from datetime import UTC, datetime

from bet.modeling.types import ProbabilityEstimate
from bet.value.detector import MinimumEdgeDetector
from bet.value.types import MarketLine, ValueBet


def _make_estimate(
    home_win: float = 0.55,
    away_win: float | None = None,
    draw: float | None = None,
) -> ProbabilityEstimate:
    if away_win is None:
        away_win = 1.0 - home_win - (draw or 0.0)
    return ProbabilityEstimate(
        event_id="game-1",
        model_id="test",
        generated_at=datetime(2023, 10, 1, tzinfo=UTC),
        home_win=home_win,
        away_win=away_win,
        draw=draw,
    )


def _make_line(
    side: str,
    decimal_odds: float,
    market_id: str = "m1",
) -> MarketLine:
    return MarketLine(
        market_id=market_id,
        side=side,
        decimal_odds=decimal_odds,
        implied_prob=1.0 / decimal_odds,
    )


class TestMinimumEdgeDetectorDetect:
    def test_returns_value_bet_when_edge_exceeds_threshold(self) -> None:
        # 0.55 × 2.10 − 1 = 0.155 > 0.02
        detector = MinimumEdgeDetector(min_edge=0.02)
        result = detector.detect(
            _make_estimate(home_win=0.55), [_make_line("home_win", 2.10)]
        )
        assert len(result) == 1
        assert result[0].side == "home_win"

    def test_returns_empty_when_no_edge(self) -> None:
        # 0.40 × 2.10 − 1 = −0.16 < 0.02
        detector = MinimumEdgeDetector(min_edge=0.02)
        result = detector.detect(
            _make_estimate(home_win=0.40), [_make_line("home_win", 2.10)]
        )
        assert result == []

    def test_empty_lines_returns_empty(self) -> None:
        detector = MinimumEdgeDetector()
        assert detector.detect(_make_estimate(), []) == []

    def test_respects_custom_min_edge_threshold(self) -> None:
        # 0.52 × 2.10 − 1 = 0.092, below min_edge=0.10
        detector = MinimumEdgeDetector(min_edge=0.10)
        result = detector.detect(
            _make_estimate(home_win=0.52), [_make_line("home_win", 2.10)]
        )
        assert result == []

    def test_detects_away_win_side(self) -> None:
        # 0.70 × 1.50 − 1 = 0.05 > 0.02
        detector = MinimumEdgeDetector(min_edge=0.02)
        estimate = _make_estimate(home_win=0.30, away_win=0.70)
        result = detector.detect(estimate, [_make_line("away_win", 1.50)])
        assert len(result) == 1
        assert result[0].side == "away_win"

    def test_detects_draw_side(self) -> None:
        # 0.25 × 5.0 − 1 = 0.25 > 0.05
        detector = MinimumEdgeDetector(min_edge=0.05)
        estimate = _make_estimate(home_win=0.40, away_win=0.35, draw=0.25)
        result = detector.detect(estimate, [_make_line("draw", 5.0)])
        assert len(result) == 1

    def test_ignores_draw_when_model_has_no_draw(self) -> None:
        detector = MinimumEdgeDetector(min_edge=0.02)
        estimate = _make_estimate(home_win=0.55, away_win=0.45)
        result = detector.detect(estimate, [_make_line("draw", 4.0)])
        assert result == []

    def test_ignores_unknown_side(self) -> None:
        detector = MinimumEdgeDetector(min_edge=0.02)
        result = detector.detect(_make_estimate(), [_make_line("unknown_side", 2.0)])
        assert result == []

    def test_detects_multiple_value_bets_across_lines(self) -> None:
        # Both sides have edge above 0.02
        # home: 0.55 × 2.10 − 1 = 0.155
        # away: 0.45 × 2.30 − 1 = 0.035
        detector = MinimumEdgeDetector(min_edge=0.02)
        estimate = _make_estimate(home_win=0.55, away_win=0.45)
        lines = [
            _make_line("home_win", 2.10, market_id="m1"),
            _make_line("away_win", 2.30, market_id="m2"),
        ]
        result = detector.detect(estimate, lines)
        assert len(result) == 2

    def test_value_bet_fields_are_correct(self) -> None:
        detector = MinimumEdgeDetector(min_edge=0.02)
        estimate = _make_estimate(home_win=0.55)
        vb = detector.detect(estimate, [_make_line("home_win", 2.10)])[0]
        assert vb.event_id == "game-1"
        assert vb.model_prob == 0.55
        assert vb.decimal_odds == 2.10
        assert abs(vb.edge - 0.155) < 1e-9

    def test_value_bet_is_correct_type(self) -> None:
        detector = MinimumEdgeDetector(min_edge=0.02)
        result = detector.detect(
            _make_estimate(home_win=0.55), [_make_line("home_win", 2.10)]
        )
        assert isinstance(result[0], ValueBet)

    def test_edge_exactly_at_threshold_is_detected(self) -> None:
        # min_edge=0.155 and EV=0.155 → should be included (>=)
        detector = MinimumEdgeDetector(min_edge=0.155)
        result = detector.detect(
            _make_estimate(home_win=0.55), [_make_line("home_win", 2.10)]
        )
        assert len(result) == 1

    def test_detected_at_matches_estimate_generated_at(self) -> None:
        detector = MinimumEdgeDetector(min_edge=0.02)
        estimate = _make_estimate(home_win=0.55)
        vb = detector.detect(estimate, [_make_line("home_win", 2.10)])[0]
        assert vb.detected_at == estimate.generated_at

    def test_max_odds_filters_out_bets_above_threshold(self) -> None:
        # Arrange — model says 0.55 on home at 2.10 odds (EV > 0.02)
        # but max_odds=2.0 should block it
        detector = MinimumEdgeDetector(min_edge=0.02, max_odds=2.0)
        estimate = _make_estimate(home_win=0.55)

        # Act
        result = detector.detect(estimate, [_make_line("home_win", 2.10)])

        # Assert
        assert result == []

    def test_max_odds_allows_bets_at_or_below_threshold(self) -> None:
        # Arrange — home bet at exactly max_odds should be allowed
        detector = MinimumEdgeDetector(min_edge=0.02, max_odds=2.10)
        estimate = _make_estimate(home_win=0.55)

        # Act
        result = detector.detect(estimate, [_make_line("home_win", 2.10)])

        # Assert
        assert len(result) == 1

    def test_no_max_odds_allows_all_qualifying_bets(self) -> None:
        # Arrange — default max_odds is infinity; high-odds bet still allowed
        detector = MinimumEdgeDetector(min_edge=0.02)
        estimate = _make_estimate(home_win=0.55)

        # Act
        result = detector.detect(estimate, [_make_line("home_win", 10.0)])

        # Assert — 0.55 × 10.0 − 1 = 4.5 > 0.02, so it should be detected
        assert len(result) == 1
