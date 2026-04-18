"""Performance metrics for a set of settled bets."""

from __future__ import annotations

import statistics

from bet.calibration.metrics import brier_score as _brier_score
from bet.calibration.metrics import expected_calibration_error as _ece
from bet.calibration.metrics import log_loss as _log_loss

from .types import BetResult, PerformanceReport


def compute_performance_report(results: list[BetResult]) -> PerformanceReport:
    """Compute aggregate performance statistics from a list of settled bets.

    Args:
        results: Settled bet outcomes. Empty list returns a zero report with
            all calibration fields set to None.

    Returns:
        PerformanceReport with ROI, win rate, drawdown, Sharpe, CLV, and
        calibration stats (Brier score, log-loss, ECE).
    """
    if not results:
        return PerformanceReport(
            total_bets=0,
            won_bets=0,
            lost_bets=0,
            total_staked=0.0,
            total_profit=0.0,
            roi=0.0,
            win_rate=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            avg_clv=None,
        )

    total_bets = len(results)
    won_bets = sum(1 for r in results if r.won)
    total_staked = sum(r.stake for r in results)
    total_profit = sum(r.pnl for r in results)
    pnls = [r.pnl for r in results]

    roi = total_profit / total_staked if total_staked > 0.0 else 0.0
    win_rate = won_bets / total_bets

    clvs = [r.clv for r in results if r.clv is not None]
    avg_clv = sum(clvs) / len(clvs) if clvs else None

    probs = [r.model_prob for r in results]
    outcomes = [int(r.won) for r in results]

    return PerformanceReport(
        total_bets=total_bets,
        won_bets=won_bets,
        lost_bets=total_bets - won_bets,
        total_staked=total_staked,
        total_profit=total_profit,
        roi=roi,
        win_rate=win_rate,
        max_drawdown=_max_drawdown(pnls),
        sharpe_ratio=_sharpe_ratio(pnls),
        avg_clv=avg_clv,
        brier_score=_brier_score(probs, outcomes),
        log_loss=_log_loss(probs, outcomes),
        calibration_error=_ece(probs, outcomes),
    )


def _max_drawdown(pnls: list[float]) -> float:
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in pnls:
        cum += pnl
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    return max_dd


def _sharpe_ratio(pnls: list[float]) -> float:
    if len(pnls) < 2:
        return 0.0
    mean = statistics.mean(pnls)
    std = statistics.stdev(pnls)
    return mean / std if std > 0.0 else 0.0
