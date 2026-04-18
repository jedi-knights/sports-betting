"""Domain types for the Value Analysis context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketLine:
    """A single offered line from a bookmaker for one outcome.

    Carries the deviggged implied probability alongside the raw decimal odds
    so callers can compare model probability against the true market estimate
    (market_prob) while computing EV from the payoff (decimal_odds).

    Attributes:
        market_id: Identifier matching the Market Data context's Market.
        side: Which outcome this line prices — ``"home_win"``, ``"away_win"``,
            or ``"draw"``.
        decimal_odds: Offered payout including stake (e.g. 2.10 returns £2.10
            per £1.00 staked).
        implied_prob: Deviggged implied probability — the market's true
            estimate of the outcome after removing the bookmaker's margin.
    """

    market_id: str
    side: str
    decimal_odds: float
    implied_prob: float


@dataclass
class EdgeEstimate:
    """Raw expected-value calculation for one market side.

    Computed before any minimum-edge filter. Negative-edge estimates are
    discarded by the detector; positive-edge estimates become ValueBets.

    Attributes:
        event_id: Identifier matching the Market Data context's Event.
        market_id: Identifier matching the Market Data context's Market.
        side: Which outcome — ``"home_win"``, ``"away_win"``, or ``"draw"``.
        model_prob: Calibrated model probability for this side.
        market_prob: Deviggged implied probability from offered odds.
        decimal_odds: Offered decimal odds.
        edge: EV per unit staked = ``model_prob × decimal_odds − 1``.
    """

    event_id: str
    market_id: str
    side: str
    model_prob: float
    market_prob: float
    decimal_odds: float
    edge: float


@dataclass
class ValueBet:
    """A detected positive-EV bet opportunity that exceeded the edge threshold.

    Attributes:
        event_id: Identifier matching the Market Data context's Event.
        market_id: Identifier matching the Market Data context's Market.
        side: Which outcome — ``"home_win"``, ``"away_win"``, or ``"draw"``.
        model_prob: Calibrated model probability for this side.
        market_prob: Deviggged implied probability from offered odds.
        decimal_odds: Offered decimal odds.
        edge: EV per unit staked = ``model_prob × decimal_odds − 1``.
        detected_at: Timestamp when this opportunity was identified.
    """

    event_id: str
    market_id: str
    side: str
    model_prob: float
    market_prob: float
    decimal_odds: float
    edge: float
    detected_at: datetime


@dataclass
class CLVResult:
    """Closing line value computed after a game closes.

    Positive CLV means the bet obtained better odds than the closing line —
    the standard evidence of genuine predictive edge independent of outcomes.

    Attributes:
        value_bet: The original bet whose closing line value is being measured.
        closing_decimal_odds: Final odds posted before game time.
        closing_prob: Implied probability at close = ``1 / closing_decimal_odds``.
        clv: ``closing_prob − (1 / value_bet.decimal_odds)``.
            Positive = beat the closing line.
    """

    value_bet: ValueBet
    closing_decimal_odds: float
    closing_prob: float
    clv: float
