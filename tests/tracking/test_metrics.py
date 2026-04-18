"""Tests for bet tracking performance metrics."""

from __future__ import annotations

from bet.tracking.metrics import compute_performance_report
from bet.tracking.types import BetResult, PerformanceReport


def _win(stake: float = 100.0, odds: float = 2.0, clv: float | None = None) -> BetResult:
    return BetResult(
        bet_id="b",
        stake=stake,
        decimal_odds=odds,
        model_prob=0.55,
        edge=0.10,
        won=True,
        pnl=stake * (odds - 1.0),
        clv=clv,
    )


def _loss(stake: float = 100.0, odds: float = 2.0, clv: float | None = None) -> BetResult:
    return BetResult(
        bet_id="b",
        stake=stake,
        decimal_odds=odds,
        model_prob=0.55,
        edge=0.10,
        won=False,
        pnl=-stake,
        clv=clv,
    )


class TestComputePerformanceReport:
    def test_returns_performance_report(self) -> None:
        result = compute_performance_report([_win()])
        assert isinstance(result, PerformanceReport)

    def test_empty_results_returns_zero_report(self) -> None:
        report = compute_performance_report([])
        assert report.total_bets == 0
        assert report.total_staked == 0.0
        assert report.total_profit == 0.0
        assert report.roi == 0.0
        assert report.win_rate == 0.0
        assert report.avg_clv is None

    def test_single_win_roi(self) -> None:
        # stake=100, odds=2.0 → pnl=100 → roi=100/100=1.0
        report = compute_performance_report([_win(stake=100.0, odds=2.0)])
        assert abs(report.roi - 1.0) < 1e-9

    def test_single_loss_roi(self) -> None:
        # stake=100, lost → pnl=-100 → roi=-1.0
        report = compute_performance_report([_loss(stake=100.0)])
        assert abs(report.roi - (-1.0)) < 1e-9

    def test_total_staked_is_sum(self) -> None:
        results = [_win(stake=100.0), _loss(stake=50.0)]
        report = compute_performance_report(results)
        assert abs(report.total_staked - 150.0) < 1e-9

    def test_total_profit_is_sum_of_pnls(self) -> None:
        # win: +100, loss: -50 → profit=50
        results = [_win(stake=100.0, odds=2.0), _loss(stake=50.0)]
        report = compute_performance_report(results)
        assert abs(report.total_profit - 50.0) < 1e-9

    def test_win_rate_all_wins(self) -> None:
        report = compute_performance_report([_win(), _win()])
        assert report.win_rate == 1.0

    def test_win_rate_all_losses(self) -> None:
        report = compute_performance_report([_loss(), _loss()])
        assert report.win_rate == 0.0

    def test_win_rate_mixed(self) -> None:
        report = compute_performance_report([_win(), _win(), _loss()])
        assert abs(report.win_rate - 2 / 3) < 1e-9

    def test_won_and_lost_bets_count(self) -> None:
        report = compute_performance_report([_win(), _win(), _loss()])
        assert report.won_bets == 2
        assert report.lost_bets == 1
        assert report.total_bets == 3

    def test_max_drawdown_computed(self) -> None:
        # pnls: [10, -20, 15, -5] → cumulative [10, -10, 5, 0]
        # peak=10, max drawdown = 10 - (-10) = 20
        results = [
            BetResult("b", 10.0, 2.0, 0.5, 0.0, True, 10.0),
            BetResult("b", 20.0, 2.0, 0.5, 0.0, False, -20.0),
            BetResult("b", 15.0, 2.0, 0.5, 0.0, True, 15.0),
            BetResult("b", 5.0, 2.0, 0.5, 0.0, False, -5.0),
        ]
        report = compute_performance_report(results)
        assert abs(report.max_drawdown - 20.0) < 1e-9

    def test_no_drawdown_on_monotone_profit(self) -> None:
        results = [
            BetResult("b", 10.0, 2.0, 0.5, 0.0, True, 10.0),
            BetResult("b", 10.0, 2.0, 0.5, 0.0, True, 10.0),
        ]
        report = compute_performance_report(results)
        assert report.max_drawdown == 0.0

    def test_avg_clv_with_data(self) -> None:
        results = [_win(clv=0.05), _loss(clv=-0.03), _win(clv=0.02)]
        report = compute_performance_report(results)
        expected = (0.05 + (-0.03) + 0.02) / 3
        assert report.avg_clv is not None
        assert abs(report.avg_clv - expected) < 1e-9

    def test_avg_clv_none_when_no_clv_data(self) -> None:
        report = compute_performance_report([_win(), _loss()])
        assert report.avg_clv is None

    def test_avg_clv_skips_none_entries(self) -> None:
        results = [_win(clv=0.04), _loss(clv=None)]
        report = compute_performance_report(results)
        assert report.avg_clv is not None
        assert abs(report.avg_clv - 0.04) < 1e-9

    def test_sharpe_ratio_zero_for_constant_pnl(self) -> None:
        # All same P&L → std=0 → Sharpe=0
        results = [_win() for _ in range(5)]
        report = compute_performance_report(results)
        assert report.sharpe_ratio == 0.0

    def test_sharpe_ratio_single_bet_is_zero(self) -> None:
        report = compute_performance_report([_win()])
        assert report.sharpe_ratio == 0.0

    # ------------------------------------------------------------------ #
    # Calibration metrics (Brier score, log-loss, ECE)                    #
    # ------------------------------------------------------------------ #

    def test_report_includes_brier_score(self) -> None:
        # Arrange
        results = [
            BetResult("b1", 100.0, 2.0, 0.7, 0.1, True, 100.0),
            BetResult("b2", 100.0, 2.0, 0.3, 0.1, False, -100.0),
        ]

        # Act
        report = compute_performance_report(results)

        # Assert
        assert isinstance(report.brier_score, float)

    def test_report_brier_score_perfect_predictions(self) -> None:
        # Arrange — model_prob matches outcome exactly
        results = [
            BetResult("b1", 100.0, 2.0, 1.0, 0.1, True, 100.0),
            BetResult("b2", 100.0, 2.0, 0.0, 0.1, False, -100.0),
        ]

        # Act
        report = compute_performance_report(results)

        # Assert
        assert report.brier_score is not None
        assert abs(report.brier_score - 0.0) < 1e-9

    def test_report_brier_score_random_predictions(self) -> None:
        # Arrange — model_prob always 0.5 → Brier score = 0.25
        results = [
            BetResult("b1", 100.0, 2.0, 0.5, 0.0, True, 100.0),
            BetResult("b2", 100.0, 2.0, 0.5, 0.0, False, -100.0),
        ]

        # Act
        report = compute_performance_report(results)

        # Assert
        assert report.brier_score is not None
        assert abs(report.brier_score - 0.25) < 1e-9

    def test_report_includes_log_loss(self) -> None:
        # Arrange
        results = [
            BetResult("b1", 100.0, 2.0, 0.7, 0.1, True, 100.0),
            BetResult("b2", 100.0, 2.0, 0.3, 0.1, False, -100.0),
        ]

        # Act
        report = compute_performance_report(results)

        # Assert
        assert isinstance(report.log_loss, float)

    def test_report_includes_calibration_error(self) -> None:
        # Arrange
        results = [
            BetResult("b1", 100.0, 2.0, 0.7, 0.1, True, 100.0),
            BetResult("b2", 100.0, 2.0, 0.3, 0.1, False, -100.0),
        ]

        # Act
        report = compute_performance_report(results)

        # Assert
        assert isinstance(report.calibration_error, float)

    def test_report_empty_results_gives_none_metrics(self) -> None:
        # Arrange / Act
        report = compute_performance_report([])

        # Assert
        assert report.brier_score is None
        assert report.log_loss is None
        assert report.calibration_error is None
