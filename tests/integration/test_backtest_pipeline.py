"""Integration tests for the walk-forward backtest pipeline.

Each test loads a small generated CSV fixture (written to a tmp_path), runs the
full pipeline — loader → extractor → model → calibrate → value → size → record —
and asserts structural correctness of the output.

These tests are deliberately sport-wide rather than unit tests of individual
components. Their purpose is to catch regressions where a new sport or model
combination fails silently (returns 0 results) or raises unexpectedly.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from bet.backtesting.loader import CSVDataLoader
from bet.backtesting.pipeline import BacktestPipeline
from bet.features.mlb import MLBFeatureExtractor
from bet.features.nba import NBAFeatureExtractor
from bet.features.nfl import NFLFeatureExtractor
from bet.features.nhl import NHLFeatureExtractor
from bet.features.soccer import SoccerFeatureExtractor
from bet.modeling.elo import EloModel
from bet.modeling.ensemble import EnsembleModel
from bet.modeling.gradient_boosting import GradientBoostingModel
from bet.modeling.logistic import LogisticRegressionModel
from bet.modeling.poisson import PoissonModel
from bet.modeling.quantile import QuantileRegressionModel
from bet.sizing.kelly import KellySizer
from bet.tracking.types import BetResult
from bet.value.detector import MinimumEdgeDetector

# ---------------------------------------------------------------------------
# Fixture generation helpers
# ---------------------------------------------------------------------------

_CSV_HEADER = (
    "event_id,sport,home_team,away_team,game_date,"
    "home_score,away_score,home_win_odds,away_win_odds,draw_odds,"
    "closing_home_win_odds,closing_away_win_odds,closing_draw_odds"
)

_TEAMS_BINARY = ["alpha", "bravo", "charlie", "delta", "echo"]
_TEAMS_SOCCER = ["ajax", "barca", "chelsea", "dortmund", "everton"]


def _write_binary_fixture(
    path: Path,
    sport: str,
    n_games: int = 40,
    home_scores: tuple[int, int] = (24, 17),
    away_scores: tuple[int, int] = (14, 21),
) -> Path:
    """Write a small binary-outcome fixture CSV (no draws)."""
    base = datetime(2023, 9, 1, tzinfo=UTC)
    rows = []
    teams = _TEAMS_BINARY
    for i in range(n_games):
        home = teams[i % len(teams)]
        away = teams[(i + 1) % len(teams)]
        # Alternate home wins and away wins so both classes appear in training.
        if i % 3 != 0:
            hs, as_ = home_scores
        else:
            hs, as_ = away_scores
        game_date = (base + timedelta(days=i * 7)).isoformat()
        rows.append(
            f"{sport}_{i:03d},{sport},{home},{away},{game_date},{hs},{as_},1.80,2.10,,1.82,2.08,"
        )
    with path.open("w") as f:
        f.write(_CSV_HEADER + "\n")
        f.write("\n".join(rows) + "\n")
    return path


def _write_soccer_fixture(path: Path, n_games: int = 40) -> Path:
    """Write a small soccer fixture CSV with draw odds."""
    base = datetime(2023, 8, 1, tzinfo=UTC)
    rows = []
    teams = _TEAMS_SOCCER
    for i in range(n_games):
        home = teams[i % len(teams)]
        away = teams[(i + 2) % len(teams)]
        # Cycle through home win, draw, away win
        if i % 3 == 0:
            hs, as_ = 2, 1
        elif i % 3 == 1:
            hs, as_ = 1, 1
        else:
            hs, as_ = 0, 2
        game_date = (base + timedelta(days=i * 7)).isoformat()
        rows.append(
            f"soccer_{i:03d},soccer,{home},{away},{game_date},"
            f"{hs},{as_},2.10,3.40,3.20,2.05,3.45,3.25"
        )
    with path.open("w") as f:
        f.write(_CSV_HEADER + "\n")
        f.write("\n".join(rows) + "\n")
    return path


def _run_pipeline(
    model,
    extractor,
    games_path: Path,
    min_edge: float = 0.0,
    min_train: int = 20,
) -> list[BetResult]:
    """Load games from path and run the full backtest pipeline."""
    games = CSVDataLoader().load(str(games_path))
    pipeline = BacktestPipeline(
        model=model,
        extractor=extractor,
        detector=MinimumEdgeDetector(min_edge=min_edge),
        sizer=KellySizer(fraction=0.25),
        bankroll=1000.0,
        min_train_games=min_train,
    )
    return pipeline.run(games)


# ---------------------------------------------------------------------------
# NFL
# ---------------------------------------------------------------------------


class TestNFLBacktest:
    def test_elo_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(tmp_path / "nfl.csv", "nfl")

        # Act
        results = _run_pipeline(
            EloModel(),
            NFLFeatureExtractor(),
            fixture,
        )

        # Assert — with min_edge=0 every game should generate at least one bet
        assert len(results) > 0

    def test_logistic_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(tmp_path / "nfl.csv", "nfl")

        # Act
        results = _run_pipeline(
            LogisticRegressionModel(),
            NFLFeatureExtractor(),
            fixture,
        )

        # Assert
        assert len(results) > 0

    def test_gradient_boosting_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(tmp_path / "nfl.csv", "nfl")

        # Act
        results = _run_pipeline(
            GradientBoostingModel(),
            NFLFeatureExtractor(),
            fixture,
        )

        # Assert
        assert len(results) > 0

    def test_quantile_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(tmp_path / "nfl.csv", "nfl")

        # Act
        results = _run_pipeline(
            QuantileRegressionModel(),
            NFLFeatureExtractor(),
            fixture,
        )

        # Assert
        assert len(results) > 0

    def test_ensemble_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(tmp_path / "nfl.csv", "nfl")
        ensemble = EnsembleModel([EloModel(), LogisticRegressionModel()])

        # Act
        results = _run_pipeline(ensemble, NFLFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0

    def test_all_results_have_valid_probabilities(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(tmp_path / "nfl.csv", "nfl")

        # Act
        results = _run_pipeline(EloModel(), NFLFeatureExtractor(), fixture)

        # Assert
        for r in results:
            assert 0.0 < r.model_prob < 1.0, f"invalid model_prob: {r.model_prob}"
            assert r.stake > 0.0, f"non-positive stake: {r.stake}"


# ---------------------------------------------------------------------------
# NBA
# ---------------------------------------------------------------------------


class TestNBABacktest:
    def test_elo_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange — NBA uses higher scores; rest-day spacing is shorter
        fixture = _write_binary_fixture(
            tmp_path / "nba.csv",
            "nba",
            home_scores=(112, 98),
            away_scores=(95, 108),
        )

        # Act
        results = _run_pipeline(EloModel(), NBAFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0

    def test_logistic_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(
            tmp_path / "nba.csv",
            "nba",
            home_scores=(112, 98),
            away_scores=(95, 108),
        )

        # Act
        results = _run_pipeline(LogisticRegressionModel(), NBAFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0

    def test_gradient_boosting_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(
            tmp_path / "nba.csv",
            "nba",
            home_scores=(112, 98),
            away_scores=(95, 108),
        )

        # Act
        results = _run_pipeline(GradientBoostingModel(), NBAFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0


# ---------------------------------------------------------------------------
# MLB
# ---------------------------------------------------------------------------


class TestMLBBacktest:
    def test_elo_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange — MLB uses low scores; games are played almost daily
        fixture = _write_binary_fixture(
            tmp_path / "mlb.csv",
            "mlb",
            home_scores=(5, 2),
            away_scores=(2, 6),
        )

        # Act
        results = _run_pipeline(EloModel(), MLBFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0

    def test_logistic_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(
            tmp_path / "mlb.csv",
            "mlb",
            home_scores=(5, 2),
            away_scores=(2, 6),
        )

        # Act
        results = _run_pipeline(LogisticRegressionModel(), MLBFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0

    def test_quantile_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(
            tmp_path / "mlb.csv",
            "mlb",
            home_scores=(5, 2),
            away_scores=(2, 6),
        )

        # Act
        results = _run_pipeline(QuantileRegressionModel(), MLBFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0


# ---------------------------------------------------------------------------
# NHL
# ---------------------------------------------------------------------------


class TestNHLBacktest:
    def test_elo_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange — NHL low-scoring; outcomes treated as binary (no draws)
        fixture = _write_binary_fixture(
            tmp_path / "nhl.csv",
            "nhl",
            home_scores=(3, 1),
            away_scores=(1, 4),
        )

        # Act
        results = _run_pipeline(EloModel(), NHLFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0

    def test_logistic_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_binary_fixture(
            tmp_path / "nhl.csv",
            "nhl",
            home_scores=(3, 1),
            away_scores=(1, 4),
        )

        # Act
        results = _run_pipeline(LogisticRegressionModel(), NHLFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0


# ---------------------------------------------------------------------------
# Soccer
# ---------------------------------------------------------------------------


class TestSoccerBacktest:
    def test_poisson_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_soccer_fixture(tmp_path / "soccer.csv")

        # Act
        results = _run_pipeline(PoissonModel(), SoccerFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0

    def test_logistic_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange — logistic regression on attack/defense strength features
        fixture = _write_soccer_fixture(tmp_path / "soccer.csv")

        # Act
        results = _run_pipeline(LogisticRegressionModel(), SoccerFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0

    def test_gradient_boosting_pipeline_produces_results(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_soccer_fixture(tmp_path / "soccer.csv")

        # Act
        results = _run_pipeline(GradientBoostingModel(), SoccerFeatureExtractor(), fixture)

        # Assert
        assert len(results) > 0

    def test_all_results_have_valid_probabilities(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_soccer_fixture(tmp_path / "soccer.csv")

        # Act
        results = _run_pipeline(PoissonModel(), SoccerFeatureExtractor(), fixture)

        # Assert
        for r in results:
            assert 0.0 < r.model_prob < 1.0, f"invalid model_prob: {r.model_prob}"


# ---------------------------------------------------------------------------
# Lookahead bias guard
# ---------------------------------------------------------------------------


class TestLookaheadGuard:
    def test_pipeline_never_uses_future_games_for_training(self, tmp_path: Path) -> None:
        # Arrange — all games on the same date would trigger the guard if future data leaked
        base = datetime(2023, 9, 1, tzinfo=UTC)
        rows = []
        header = _CSV_HEADER
        for i in range(30):
            game_date = (base + timedelta(days=i)).isoformat()
            rows.append(f"nfl_{i:03d},nfl,alpha,bravo,{game_date},24,17,1.80,2.10,,1.82,2.08,")
        path = tmp_path / "sequential.csv"
        path.write_text(header + "\n" + "\n".join(rows) + "\n")

        # Act — should complete without AssertionError from the lookahead guard
        results = _run_pipeline(EloModel(), NFLFeatureExtractor(), path)

        # Assert — we just need it not to raise; result count may be small
        assert isinstance(results, list)
