"""Tests for the walk-forward backtesting pipeline."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from bet.backtesting.pipeline import BacktestPipeline
from bet.backtesting.types import HistoricalGame
from bet.features.nfl import NFLFeatureExtractor
from bet.modeling.elo import EloModel
from bet.sizing.kelly import KellySizer
from bet.tracking.metrics import compute_performance_report
from bet.tracking.types import BetResult
from bet.value.detector import MinimumEdgeDetector


def _make_nfl_games(n: int = 40, seed: int = 42) -> list[HistoricalGame]:
    rng = random.Random(seed)
    teams = ["TeamA", "TeamB", "TeamC", "TeamD", "TeamE", "TeamF"]
    base = datetime(2023, 9, 7, 20, 0, 0, tzinfo=UTC)
    games = []
    for i in range(n):
        home = teams[i % len(teams)]
        away = teams[(i + 3) % len(teams)]
        game_date = base + timedelta(weeks=i // 3)
        games.append(
            HistoricalGame(
                event_id=f"nfl-{i}",
                sport="nfl",
                home_team=home,
                away_team=away,
                game_date=game_date,
                home_score=rng.randint(7, 42),
                away_score=rng.randint(7, 35),
                home_win_odds=2.10,
                away_win_odds=2.10,
                draw_odds=None,
                closing_home_win_odds=2.05,
                closing_away_win_odds=2.15,
                closing_draw_odds=None,
            )
        )
    return games


def _make_pipeline(min_edge: float = 0.0, min_train: int = 10) -> BacktestPipeline:
    return BacktestPipeline(
        model=EloModel(),
        extractor=NFLFeatureExtractor(),
        detector=MinimumEdgeDetector(min_edge=min_edge),
        sizer=KellySizer(fraction=0.25),
        bankroll=1000.0,
        min_train_games=min_train,
    )


class TestBacktestPipelineRun:
    def test_returns_list(self) -> None:
        pipeline = _make_pipeline()
        result = pipeline.run(_make_nfl_games(15))
        assert isinstance(result, list)

    def test_empty_games_returns_empty(self) -> None:
        pipeline = _make_pipeline()
        assert pipeline.run([]) == []

    def test_skips_games_before_min_train(self) -> None:
        # With 5 games and min_train=10, pipeline processes none
        pipeline = _make_pipeline(min_train=10)
        assert pipeline.run(_make_nfl_games(5)) == []

    def test_results_are_bet_result_instances(self) -> None:
        pipeline = _make_pipeline(min_edge=0.0, min_train=5)
        results = pipeline.run(_make_nfl_games(20))
        assert all(isinstance(r, BetResult) for r in results)

    def test_integration_elo_nfl_fixture(self) -> None:
        # Full pipeline run: should complete without exceptions and find bets
        # Elo home-advantage gives ~0.59 home probability; at 2.10 odds EV≈0.24>0
        pipeline = _make_pipeline(min_edge=0.0, min_train=10)
        results = pipeline.run(_make_nfl_games(40))
        assert len(results) > 0

    def test_results_have_valid_pnl(self) -> None:
        pipeline = _make_pipeline(min_edge=0.0, min_train=10)
        results = pipeline.run(_make_nfl_games(30))
        for r in results:
            if r.won:
                assert r.pnl > 0
            else:
                assert r.pnl < 0

    def test_performance_report_computable(self) -> None:
        pipeline = _make_pipeline(min_edge=0.0, min_train=10)
        results = pipeline.run(_make_nfl_games(30))
        report = compute_performance_report(results)
        assert report.total_bets == len(results)

    def test_clv_attached_to_results(self) -> None:
        pipeline = _make_pipeline(min_edge=0.0, min_train=10)
        results = pipeline.run(_make_nfl_games(20))
        for r in results:
            assert r.clv is not None

    def test_no_lookahead_bias_in_training(self) -> None:
        # Pipeline must not raise LookaheadBiasError when data is clean
        pipeline = _make_pipeline(min_edge=0.0, min_train=5)
        pipeline.run(_make_nfl_games(25))  # should not raise
