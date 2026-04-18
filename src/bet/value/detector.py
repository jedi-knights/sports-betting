"""Minimum-edge ValueDetector implementation."""

from __future__ import annotations

from ..modeling.types import ProbabilityEstimate
from .ev import expected_value
from .types import MarketLine, ValueBet


class MinimumEdgeDetector:
    """Detects value bets whose EV meets or exceeds a configurable threshold.

    For each offered line, computes EV = model_prob × decimal_odds − 1.
    Emits a ValueBet when EV ≥ min_edge.

    Args:
        min_edge: Minimum EV threshold. Defaults to 0.02 (2% edge).
            Higher values are more selective; lower values surface more bets
            at the cost of including weaker edges.
    """

    def __init__(self, min_edge: float = 0.02) -> None:
        self._min_edge = min_edge

    def detect(
        self,
        estimate: ProbabilityEstimate,
        lines: list[MarketLine],
    ) -> list[ValueBet]:
        """Scan market lines for value bets.

        Args:
            estimate: Calibrated model probabilities for one game.
            lines: Offered lines to evaluate.

        Returns:
            All ValueBets where EV ≥ min_edge, in the order the lines appear.
        """
        value_bets: list[ValueBet] = []
        for line in lines:
            model_prob = self._model_prob_for_side(estimate, line.side)
            if model_prob is None:
                continue
            edge = expected_value(model_prob, line.decimal_odds)
            if edge >= self._min_edge:
                value_bets.append(
                    ValueBet(
                        event_id=estimate.event_id,
                        market_id=line.market_id,
                        side=line.side,
                        model_prob=model_prob,
                        market_prob=line.implied_prob,
                        decimal_odds=line.decimal_odds,
                        edge=edge,
                        detected_at=estimate.generated_at,
                    )
                )
        return value_bets

    @staticmethod
    def _model_prob_for_side(
        estimate: ProbabilityEstimate,
        side: str,
    ) -> float | None:
        if side == "home_win":
            return estimate.home_win
        if side == "away_win":
            return estimate.away_win
        if side == "draw":
            return estimate.draw
        return None
