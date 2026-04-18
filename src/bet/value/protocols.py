"""Protocol for the Value Analysis context."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..modeling.types import ProbabilityEstimate
from .types import MarketLine, ValueBet


@runtime_checkable
class ValueDetector(Protocol):
    """Detects positive-EV betting opportunities.

    Compares a calibrated model's probability estimates against offered market
    lines and emits a ValueBet for each side where expected value exceeds the
    configured minimum-edge threshold.
    """

    def detect(
        self,
        estimate: ProbabilityEstimate,
        lines: list[MarketLine],
    ) -> list[ValueBet]:
        """Scan market lines for value bets.

        Args:
            estimate: Calibrated model probabilities for one game.
            lines: Offered lines to evaluate. Each line specifies a side,
                decimal odds, and deviggged implied probability.

        Returns:
            All ValueBets where EV ≥ the detector's minimum-edge threshold.
            Empty list when no lines pass the filter.
        """
        ...
