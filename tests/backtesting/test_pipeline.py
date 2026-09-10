"""Tests for the walk-forward backtesting pipeline."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest

from bet.backtesting.pipeline import BacktestPipeline
from bet.backtesting.types import HistoricalGame
from bet.features.nfl import NFLFeatureExtractor
from bet.features.soccer import SoccerFeatureExtractor
from bet.modeling.elo import EloModel
from bet.modeling.logistic import LogisticRegressionModel
from bet.modeling.poisson import PoissonModel
from bet.modeling.types import ProbabilityEstimate
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

    def test_logistic_regression_model_produces_bets(self) -> None:
        """LogisticRegressionModel needs populated feature dicts in training examples.

        The pipeline must inject computed feature vectors before calling model.fit(),
        otherwise sklearn raises ValueError: 0 feature(s) found.
        """
        # Arrange
        pipeline = BacktestPipeline(
            model=LogisticRegressionModel(),
            extractor=NFLFeatureExtractor(),
            detector=MinimumEdgeDetector(min_edge=0.0),
            sizer=KellySizer(fraction=0.25),
            bankroll=1000.0,
            min_train_games=10,
        )

        # Act
        results = pipeline.run(_make_nfl_games(40))

        # Assert — with enough training data and min_edge=0, bets must be found
        assert len(results) > 0, (
            "LogisticRegressionModel detected 0 bets — likely caused by empty "
            "feature dicts being passed to model.fit() (sklearn ValueError caught "
            "silently, all folds skipped)"
        )

    def test_no_lookahead_bias_in_training(self) -> None:
        # Pipeline must not raise LookaheadBiasError when data is clean
        pipeline = _make_pipeline(min_edge=0.0, min_train=5)
        pipeline.run(_make_nfl_games(25))  # should not raise

    def test_predictions_reflect_training_history(self) -> None:
        """Elo predictions must use team ratings built from training games.

        A team that wins every training game should be predicted as a clear
        favourite — not as the static 59% that home-advantage alone produces.
        If the extractor's fit() is never called the model has no data and
        every prediction collapses to the default home-advantage probability.
        """
        base = datetime(2023, 1, 1, tzinfo=UTC)

        # Arrange — 15 blowout wins for Dominant; Weak never scores
        train_games = [
            HistoricalGame(
                event_id=f"train-{i}",
                sport="nfl",
                home_team="Dominant",
                away_team="Weak",
                game_date=base + timedelta(weeks=i),
                home_score=35,
                away_score=0,
                home_win_odds=2.10,
                away_win_odds=2.10,
                draw_odds=None,
                closing_home_win_odds=2.10,
                closing_away_win_odds=2.10,
                closing_draw_odds=None,
            )
            for i in range(15)
        ]
        test_game = HistoricalGame(
            event_id="test-0",
            sport="nfl",
            home_team="Dominant",
            away_team="Weak",
            game_date=base + timedelta(weeks=15),
            home_score=28,
            away_score=10,
            home_win_odds=2.10,
            away_win_odds=2.10,
            draw_odds=None,
            closing_home_win_odds=2.10,
            closing_away_win_odds=2.10,
            closing_draw_odds=None,
        )
        pipeline = BacktestPipeline(
            model=EloModel(),
            extractor=NFLFeatureExtractor(),
            detector=MinimumEdgeDetector(min_edge=0.0),
            sizer=KellySizer(fraction=0.25),
            bankroll=1000.0,
            min_train_games=10,
        )

        # Act
        results = pipeline.run(train_games + [test_game])

        # Assert — Dominant has won 15/15; predicted home_prob must be >> 0.80.
        # The static home-advantage-only bug produces exactly ~0.593.
        home_result = next((r for r in results if r.bet_id == "test-0_home_win"), None)
        assert home_result is not None, "Expected a home_win bet on test-0"
        assert home_result.model_prob > 0.75, (
            f"Dominant should be predicted as a strong favourite (>0.75) "
            f"after 15 wins, but model_prob={home_result.model_prob:.4f}. "
            "Likely cause: extractor.fit() is never called by the pipeline."
        )


def _make_soccer_games(n: int = 40, seed: int = 99) -> list[HistoricalGame]:
    """Build a soccer-style game fixture with 3-way markets and low-scoring outcomes.

    Odds are realistic decimal values whose implied probabilities sum to ~1.04
    (a 4% vig), ensuring a genuine bookmaker margin without exotic values.

    Draw odds of 4.00 (implied ~0.25) are intentionally generous relative to
    the Poisson model's typical draw probability (~26-30%), so that at least
    some games produce draw-side value bets when ``min_edge=0.0``.

    Args:
        n: Number of games to generate.
        seed: Random seed for reproducibility.

    Returns:
        A list of soccer HistoricalGame instances sorted by game_date.
    """
    rng = random.Random(seed)
    teams = ["Arsenal", "Chelsea", "Liverpool", "ManCity", "Spurs", "United"]
    base = datetime(2023, 8, 12, 15, 0, 0, tzinfo=UTC)
    games = []
    for i in range(n):
        home = teams[i % len(teams)]
        away = teams[(i + 2) % len(teams)]
        game_date = base + timedelta(weeks=i // 3)
        games.append(
            HistoricalGame(
                event_id=f"soccer-{i}",
                sport="soccer",
                home_team=home,
                away_team=away,
                game_date=game_date,
                home_score=rng.randint(0, 4),
                away_score=rng.randint(0, 4),
                home_win_odds=2.40,
                away_win_odds=3.10,
                draw_odds=3.30,
                closing_home_win_odds=2.35,
                closing_away_win_odds=3.05,
                closing_draw_odds=3.25,
            )
        )
    return games


def _make_soccer_pipeline(min_edge: float = 0.0, min_train: int = 10) -> BacktestPipeline:
    """Construct a BacktestPipeline wired for the soccer / Poisson path.

    Uses ``SoccerFeatureExtractor`` and ``PoissonModel`` explicitly — the same
    combination the CLI selects for ``--sport soccer``.

    Args:
        min_edge: Minimum EV threshold forwarded to ``MinimumEdgeDetector``.
        min_train: Minimum training games before predictions are made.

    Returns:
        A configured BacktestPipeline ready to run soccer games.
    """
    return BacktestPipeline(
        model=PoissonModel(),
        extractor=SoccerFeatureExtractor(),
        detector=MinimumEdgeDetector(min_edge=min_edge),
        sizer=KellySizer(fraction=0.25),
        bankroll=1000.0,
        min_train_games=min_train,
    )


class TestBacktestPipelineSoccer:
    """Integration tests for the soccer / Poisson backtest path.

    Each test exercises the end-to-end pipeline with soccer-style fixtures:
    3-way markets (home / draw / away), decimal-odds inputs, and low integer
    scores. The class mirrors ``TestBacktestPipelineRun`` for the NFL path.
    """

    def test_soccer_pipeline_returns_list(self) -> None:
        """Pipeline run returns a list for any non-empty soccer game set."""
        # Arrange
        pipeline = _make_soccer_pipeline()

        # Act
        result = pipeline.run(_make_soccer_games(40))

        # Assert
        assert isinstance(result, list)

    def test_soccer_pipeline_bets_are_bet_result_instances(self) -> None:
        """Every element returned by the pipeline is a BetResult."""
        # Arrange
        pipeline = _make_soccer_pipeline(min_edge=0.0, min_train=10)

        # Act
        results = pipeline.run(_make_soccer_games(40))

        # Assert
        assert all(isinstance(r, BetResult) for r in results)

    def test_soccer_pipeline_produces_bets(self) -> None:
        """Pipeline detects at least one value bet across 40 soccer games.

        With min_edge=0.0 the detector flags any game where the Poisson model
        assigns higher probability than the market's implied probability. The
        fixture produces 40 games — enough training data for the model to
        estimate realistic baselines and surface positive-EV opportunities.
        """
        # Arrange
        pipeline = _make_soccer_pipeline(min_edge=0.0, min_train=10)

        # Act
        results = pipeline.run(_make_soccer_games(40))

        # Assert
        assert len(results) > 0, (
            "Soccer / Poisson pipeline returned 0 bets with min_edge=0.0 and "
            "40 games. The model or extractor is likely not producing predictions."
        )

    def test_pipeline_skips_games_without_odds(self) -> None:
        """Games with None odds (e.g. from ASA / model-only leagues) must not crash.

        The pipeline should silently skip market-line construction for games
        that have no odds and produce an empty result set rather than raising.
        """
        # Arrange — build soccer games with all odds set to None
        base = datetime(2023, 8, 1, tzinfo=UTC)
        teams = ["Ajax", "Barca", "Chelsea", "Dortmund", "Everton"]
        games = [
            HistoricalGame(
                event_id=f"nwsl-{i}",
                sport="nwsl",
                home_team=teams[i % len(teams)],
                away_team=teams[(i + 1) % len(teams)],
                game_date=base + timedelta(weeks=i),
                home_score=i % 3,
                away_score=(i + 1) % 3,
                home_win_odds=None,
                away_win_odds=None,
                draw_odds=None,
                closing_home_win_odds=None,
                closing_away_win_odds=None,
                closing_draw_odds=None,
            )
            for i in range(30)
        ]
        from bet.features.nwsl import NWSLFeatureExtractor
        from bet.modeling.poisson import PoissonModel

        pipeline = BacktestPipeline(
            model=PoissonModel(),
            extractor=NWSLFeatureExtractor(),
            detector=MinimumEdgeDetector(min_edge=0.0),
            sizer=KellySizer(fraction=0.25),
            bankroll=1000.0,
            min_train_games=10,
        )

        # Act — must not raise
        results = pipeline.run(games)

        # Assert — no odds means no market lines means no bets
        assert results == []

    def test_soccer_draw_bets_possible(self) -> None:
        """At least one bet with a _draw suffix appears in the results.

        PoissonModel computes an explicit draw probability; the pipeline
        converts it to a market line when draw_odds is not None. With generous
        draw odds (3.30 implied ~0.303 vs. Poisson draw ~25-30%) and
        min_edge=0.0 at least some games should show a draw edge.

        The fixture uses draw_odds=3.30. The Poisson model's draw probability
        depends on fitted baselines, so we use a larger game set (40 games)
        with a fixed seed that is known to produce at least one draw bet.
        """
        # Arrange — use a seed and game count calibrated to guarantee a draw bet
        games = _make_soccer_games(n=40, seed=99)
        # Lower the draw market price slightly to widen the edge window
        draw_boosted = [
            HistoricalGame(
                event_id=g.event_id,
                sport=g.sport,
                home_team=g.home_team,
                away_team=g.away_team,
                game_date=g.game_date,
                home_score=g.home_score,
                away_score=g.away_score,
                home_win_odds=g.home_win_odds,
                away_win_odds=g.away_win_odds,
                draw_odds=4.00,  # implied 0.25 — well below typical Poisson draw
                closing_home_win_odds=g.closing_home_win_odds,
                closing_away_win_odds=g.closing_away_win_odds,
                closing_draw_odds=4.00,
            )
            for g in games
        ]
        pipeline = _make_soccer_pipeline(min_edge=0.0, min_train=10)

        # Act
        results = pipeline.run(draw_boosted)

        # Assert
        draw_bets = [r for r in results if r.bet_id.endswith("_draw")]
        assert len(draw_bets) > 0, (
            "No _draw bets detected. PoissonModel should produce draw probabilities "
            "above 0.25 for some games; check that draw_odds lines are forwarded "
            "through _to_market_lines() and that the detector handles side='draw'."
        )


def _make_soccer_games_no_odds(n: int = 40, seed: int = 7) -> list[HistoricalGame]:
    """Soccer fixture with every odds column set to None.

    Mirrors the shape of the free ASA data feed (MLS / NWSL), which returns
    completed match results without any bookmaker odds.
    """
    rng = random.Random(seed)
    teams = ["Arsenal", "Chelsea", "Liverpool", "ManCity", "Spurs", "United"]
    base = datetime(2023, 8, 12, 15, 0, 0, tzinfo=UTC)
    games = []
    for i in range(n):
        home = teams[i % len(teams)]
        away = teams[(i + 2) % len(teams)]
        game_date = base + timedelta(weeks=i // 3)
        games.append(
            HistoricalGame(
                event_id=f"soccer-{i}",
                sport="soccer",
                home_team=home,
                away_team=away,
                game_date=game_date,
                home_score=rng.randint(0, 4),
                away_score=rng.randint(0, 4),
                home_win_odds=None,
                away_win_odds=None,
                draw_odds=None,
                closing_home_win_odds=None,
                closing_away_win_odds=None,
                closing_draw_odds=None,
            )
        )
    return games


class TestBacktestPipelinePredictions:
    """Tests for BacktestPipeline.predictions() — raw model outputs, no odds required."""

    def test_yields_one_estimate_per_eligible_game(self) -> None:
        # Arrange
        pipeline = _make_soccer_pipeline(min_edge=0.0, min_train=10)
        games = _make_soccer_games_no_odds(30)

        # Act
        pairs = list(pipeline.predictions(games))

        # Assert — most games past min_train_games get a prediction
        # (early folds may still skip when the extractor lacks history for a team)
        assert len(pairs) >= 15

    def test_each_pair_is_game_and_probability_estimate(self) -> None:
        # Arrange
        pipeline = _make_soccer_pipeline(min_edge=0.0, min_train=10)

        # Act
        pairs = list(pipeline.predictions(_make_soccer_games_no_odds(20)))

        # Assert
        assert all(isinstance(g, HistoricalGame) for g, _ in pairs)
        assert all(isinstance(p, ProbabilityEstimate) for _, p in pairs)

    def test_works_when_all_odds_are_none(self) -> None:
        """Predictions must not require odds — calibration only needs prob + outcome."""
        # Arrange
        pipeline = _make_soccer_pipeline(min_edge=0.0, min_train=10)
        games = _make_soccer_games_no_odds(25)
        assert all(g.home_win_odds is None for g in games)

        # Act
        pairs = list(pipeline.predictions(games))

        # Assert
        assert len(pairs) > 0

    def test_probabilities_are_valid(self) -> None:
        # Arrange
        pipeline = _make_soccer_pipeline(min_edge=0.0, min_train=10)

        # Act
        pairs = list(pipeline.predictions(_make_soccer_games_no_odds(20)))

        # Assert
        for _, est in pairs:
            assert 0.0 <= est.home_win <= 1.0
            assert 0.0 <= est.away_win <= 1.0

    def test_yielded_games_are_in_chronological_order(self) -> None:
        # Arrange
        pipeline = _make_soccer_pipeline(min_edge=0.0, min_train=10)

        # Act
        pairs = list(pipeline.predictions(_make_soccer_games_no_odds(25)))

        # Assert
        game_dates = [g.game_date for g, _ in pairs]
        assert game_dates == sorted(game_dates)

    def test_skips_games_before_min_train(self) -> None:
        # Arrange
        pipeline = _make_soccer_pipeline(min_edge=0.0, min_train=100)

        # Act
        pairs = list(pipeline.predictions(_make_soccer_games_no_odds(30)))

        # Assert
        assert pairs == []


class _CountingModel:
    """Test double that counts fit() invocations.

    Wraps PoissonModel so predictions still work; only fit_count is added.
    """

    def __init__(self) -> None:
        self._inner = PoissonModel()
        self.fit_count = 0

    @property
    def model_id(self) -> str:
        return self._inner.model_id

    def fit(self, examples: object) -> None:
        self.fit_count += 1
        self._inner.fit(examples)  # type: ignore[arg-type]

    def predict(self, features: object) -> ProbabilityEstimate:
        return self._inner.predict(features)  # type: ignore[arg-type]


class TestBacktestPipelineRefitInterval:
    """Refit interval controls how often the model is re-trained during walk-forward.

    interval=1 (default): refit at every prediction — exact walk-forward.
    interval=K: refit once every K predictions — K-fold speedup.
    """

    def test_default_interval_refits_every_prediction(self) -> None:
        # Arrange — default interval=1 refits once for every yielded prediction
        counting = _CountingModel()
        pipeline = BacktestPipeline(
            model=counting,
            extractor=SoccerFeatureExtractor(),
            detector=MinimumEdgeDetector(min_edge=0.0),
            sizer=KellySizer(fraction=0.25),
            bankroll=1000.0,
            min_train_games=10,
        )
        games = _make_soccer_games_no_odds(20)

        # Act
        pairs = list(pipeline.predictions(games))

        # Assert
        assert counting.fit_count == len(pairs)
        assert counting.fit_count > 0

    def test_interval_5_refits_once_per_5_games(self) -> None:
        # Arrange
        counting = _CountingModel()
        pipeline = BacktestPipeline(
            model=counting,
            extractor=SoccerFeatureExtractor(),
            detector=MinimumEdgeDetector(min_edge=0.0),
            sizer=KellySizer(fraction=0.25),
            bankroll=1000.0,
            min_train_games=10,
            refit_interval=5,
        )
        games = _make_soccer_games_no_odds(20)

        # Act
        list(pipeline.predictions(games))

        # Assert — 10 eligible games / 5 = 2 refits
        assert counting.fit_count == 2

    def test_interval_larger_than_games_refits_once(self) -> None:
        # Arrange
        counting = _CountingModel()
        pipeline = BacktestPipeline(
            model=counting,
            extractor=SoccerFeatureExtractor(),
            detector=MinimumEdgeDetector(min_edge=0.0),
            sizer=KellySizer(fraction=0.25),
            bankroll=1000.0,
            min_train_games=10,
            refit_interval=100,
        )
        games = _make_soccer_games_no_odds(20)

        # Act
        list(pipeline.predictions(games))

        # Assert — one refit at the first eligible game, none after
        assert counting.fit_count == 1

    def test_interval_still_yields_all_predictions(self) -> None:
        """Increasing the interval must not reduce the number of predictions —
        only reduce the frequency of refits."""
        # Arrange
        pipeline_1 = _make_soccer_pipeline(min_edge=0.0, min_train=10)
        pipeline_10 = BacktestPipeline(
            model=PoissonModel(),
            extractor=SoccerFeatureExtractor(),
            detector=MinimumEdgeDetector(min_edge=0.0),
            sizer=KellySizer(fraction=0.25),
            bankroll=1000.0,
            min_train_games=10,
            refit_interval=10,
        )
        games = _make_soccer_games_no_odds(30)

        # Act
        n_at_1 = len(list(pipeline_1.predictions(games)))
        n_at_10 = len(list(pipeline_10.predictions(games)))

        # Assert
        assert n_at_1 == n_at_10

    def test_interval_zero_rejected(self) -> None:
        # Act / Assert
        with pytest.raises(ValueError, match="refit_interval"):
            BacktestPipeline(
                model=PoissonModel(),
                extractor=SoccerFeatureExtractor(),
                detector=MinimumEdgeDetector(min_edge=0.0),
                sizer=KellySizer(fraction=0.25),
                bankroll=1000.0,
                refit_interval=0,
            )
