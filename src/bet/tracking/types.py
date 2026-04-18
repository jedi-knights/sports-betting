"""Domain types for the Bet Tracking context."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BetResult:
    """The financial outcome of a single settled bet.

    Attributes:
        bet_id: Unique identifier of the original bet signal.
        stake: Absolute amount wagered.
        decimal_odds: Odds at which the bet was placed.
        model_prob: Calibrated model probability for the outcome.
        edge: EV per unit staked at bet placement time.
        won: True if the outcome was correct.
        pnl: Profit or loss in stake units. Positive = profit, negative = loss.
        clv: Closing line value. None if not tracked.
    """

    bet_id: str
    stake: float
    decimal_odds: float
    model_prob: float
    edge: float
    won: bool
    pnl: float
    clv: float | None = None


@dataclass
class PerformanceReport:
    """Aggregate performance statistics for a set of settled bets.

    Attributes:
        total_bets: Number of bets in the report.
        won_bets: Number of winning bets.
        lost_bets: Number of losing bets.
        total_staked: Sum of all stakes.
        total_profit: Sum of all P&L values.
        roi: total_profit / total_staked. 0.0 when no bets.
        win_rate: won_bets / total_bets. 0.0 when no bets.
        max_drawdown: Largest peak-to-trough drop in cumulative P&L.
        sharpe_ratio: mean(pnl) / std(pnl) per bet. 0.0 when std is zero.
        avg_clv: Mean closing line value. None when no CLV data is available.
        brier_score: Mean squared error between model probabilities and
            outcomes. None when results is empty.
        log_loss: Negative log-likelihood between model probabilities and
            outcomes. None when results is empty.
        calibration_error: Expected calibration error (ECE) across 10 bins.
            None when results is empty.
    """

    total_bets: int
    won_bets: int
    lost_bets: int
    total_staked: float
    total_profit: float
    roi: float
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    avg_clv: float | None
    brier_score: float | None = None
    log_loss: float | None = None
    calibration_error: float | None = None
