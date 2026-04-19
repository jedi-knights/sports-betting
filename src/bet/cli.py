"""Entry point for the bet CLI."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

import click

from .backtesting.loader import CSVDataLoader
from .backtesting.pipeline import BacktestPipeline
from .calibration.isotonic import IsotonicCalibrator
from .calibration.metrics import brier_score, expected_calibration_error, log_loss
from .calibration.model import CalibratedModel
from .features.ecnl import ECNLFeatureExtractor
from .features.ecrl import ECRLFeatureExtractor
from .features.epl import EPLFeatureExtractor
from .features.mlb import MLBFeatureExtractor
from .features.mls import MLSFeatureExtractor
from .features.nba import NBAFeatureExtractor
from .features.nfl import NFLFeatureExtractor
from .features.nhl import NHLFeatureExtractor
from .features.nwsl import NWSLFeatureExtractor
from .features.usl_super_league import USLSuperLeagueFeatureExtractor
from .features.usl_w_league import USLWLeagueFeatureExtractor
from .features.wpsl import WPSLFeatureExtractor
from .modeling.elo import EloModel
from .modeling.ensemble import EnsembleModel
from .modeling.gradient_boosting import GradientBoostingModel
from .modeling.logistic import LogisticRegressionModel
from .modeling.poisson import PoissonModel
from .modeling.protocols import FeatureExtractor, Model
from .modeling.quantile import QuantileRegressionModel
from .sizing.kelly import KellySizer
from .tracking.metrics import compute_performance_report
from .value.detector import MinimumEdgeDetector

# Leagues that use the Poisson model and soccer-specific feature extractors.
_SOCCER_LEAGUES: frozenset[str] = frozenset(
    ["epl", "mls", "nwsl", "usl_super_league", "usl_w_league", "wpsl", "ecnl", "ecrl"]
)

_SPORT_CHOICES = ["nfl", "nba", "mlb", "nhl", *sorted(_SOCCER_LEAGUES)]

_EXTRACTOR_FACTORIES: dict[str, Callable[[float, bool], FeatureExtractor]] = {
    "nfl": lambda k, mov: NFLFeatureExtractor(k_factor=k, use_mov=mov),
    "nba": lambda k, mov: NBAFeatureExtractor(k_factor=k, use_mov=mov),
    "mlb": lambda k, mov: MLBFeatureExtractor(k_factor=k, use_mov=mov),
    "nhl": lambda k, mov: NHLFeatureExtractor(k_factor=k, use_mov=mov),
    "epl": lambda k, mov: EPLFeatureExtractor(),
    "mls": lambda k, mov: MLSFeatureExtractor(),
    "nwsl": lambda k, mov: NWSLFeatureExtractor(),
    "usl_super_league": lambda k, mov: USLSuperLeagueFeatureExtractor(),
    "usl_w_league": lambda k, mov: USLWLeagueFeatureExtractor(),
    "wpsl": lambda k, mov: WPSLFeatureExtractor(),
    "ecnl": lambda k, mov: ECNLFeatureExtractor(),
    "ecrl": lambda k, mov: ECRLFeatureExtractor(),
}


def _maybe_calibrate(model: Model, calibrate: bool = True) -> Model:
    """Wrap model in CalibratedModel(IsotonicCalibrator) when calibrate is True."""
    if not calibrate:
        return model
    return CalibratedModel(model, IsotonicCalibrator())


def _build_model_and_extractor(
    sport: str,
    model_name: str,
    k_factor: float,
    use_mov: bool,
) -> tuple[Model, FeatureExtractor]:
    extractor = _EXTRACTOR_FACTORIES[sport](k_factor, use_mov)

    if sport in _SOCCER_LEAGUES and model_name == "poisson":
        return PoissonModel(), extractor

    if model_name == "elo":
        return EloModel(k_factor=k_factor, use_mov=use_mov), extractor
    if model_name == "logistic":
        return LogisticRegressionModel(), extractor
    if model_name == "gradient_boosting":
        return GradientBoostingModel(), extractor
    if model_name == "quantile":
        return QuantileRegressionModel(), extractor
    if model_name == "ensemble":
        return (
            EnsembleModel(
                [EloModel(k_factor=k_factor, use_mov=use_mov), LogisticRegressionModel()]
            ),
            extractor,
        )
    # poisson is only valid for soccer and is handled above; any other model_name
    # reaching this point indicates an invalid combination of sport and model.
    raise ValueError(f"model '{model_name}' is not valid for sport '{sport}'")


@click.group()
def main() -> None:
    """Sports betting modeling and backtesting CLI."""


@main.command()
@click.option(
    "--sport",
    required=True,
    type=click.Choice(_SPORT_CHOICES),
)
@click.option("--data", required=True, type=click.Path(exists=True))
@click.option(
    "--model",
    "model_name",
    default="elo",
    type=click.Choice(["elo", "logistic", "poisson", "gradient_boosting", "quantile", "ensemble"]),
)
@click.option("--min-edge", default=0.02, show_default=True, type=float)
@click.option("--bankroll", default=1000.0, show_default=True, type=float)
@click.option("--kelly-fraction", default=0.25, show_default=True, type=float)
@click.option(
    "--min-train",
    default=20,
    show_default=True,
    type=int,
    help="Minimum training games before predicting",
)
@click.option(
    "--k-factor",
    default=20.0,
    show_default=True,
    type=float,
    help="Elo K-factor (rate of rating change per game)",
)
@click.option(
    "--no-mov",
    "use_mov",
    is_flag=True,
    default=True,
    flag_value=False,
    help="Disable margin-of-victory scaling (use binary win/loss)",
)
@click.option(
    "--max-odds",
    default=float("inf"),
    show_default=True,
    type=float,
    help="Skip bets with market odds above this value",
)
@click.option("--output", type=click.Path(), default=None)
@click.option(
    "--calibrate/--no-calibrate",
    default=True,
    show_default=True,
    help="Wrap model in isotonic calibration (recommended; matches architecture spec)",
)
def backtest(
    sport: str,
    data: str,
    model_name: str,
    min_edge: float,
    bankroll: float,
    kelly_fraction: float,
    min_train: int,
    k_factor: float,
    use_mov: bool,
    max_odds: float,
    output: str | None,
    calibrate: bool,
) -> None:
    """Run walk-forward backtesting on historical game data."""
    games = CSVDataLoader().load(data)
    click.echo(f"Loaded {len(games)} games from {data}")

    model, extractor = _build_model_and_extractor(sport, model_name, k_factor, use_mov)
    model = _maybe_calibrate(model, calibrate=calibrate)

    pipeline = BacktestPipeline(
        model=model,
        extractor=extractor,
        detector=MinimumEdgeDetector(min_edge=min_edge, max_odds=max_odds),
        sizer=KellySizer(fraction=kelly_fraction),
        bankroll=bankroll,
        min_train_games=min_train,
    )

    results = pipeline.run(games)
    report = compute_performance_report(results)

    click.echo(f"\nBacktest complete — {report.total_bets} bets detected")
    click.echo(f"  Win rate : {report.win_rate:.1%}")
    click.echo(f"  ROI      : {report.roi:.2%}")
    click.echo(f"  Max DD   : {report.max_drawdown:.2f}")
    click.echo(f"  Sharpe   : {report.sharpe_ratio:.3f}")
    if report.avg_clv is not None:
        click.echo(f"  Avg CLV  : {report.avg_clv:.4f}")
    if report.brier_score is not None:
        click.echo(f"  Brier    : {report.brier_score:.4f}")
    if report.log_loss is not None:
        click.echo(f"  Log loss : {report.log_loss:.4f}")
    if report.calibration_error is not None:
        click.echo(f"  Cal err  : {report.calibration_error:.4f}")

    if output:
        report_dict = asdict(report)
        try:
            with Path(output).open("w") as f:
                json.dump(report_dict, f, indent=2)
            click.echo(f"\nReport written to {output}")
        except OSError as exc:
            click.echo(f"Error writing report to {output}: {exc}", err=True)
            sys.exit(1)

    sys.exit(0)


@main.command()
@click.option(
    "--sport",
    required=True,
    type=click.Choice(_SPORT_CHOICES),
)
@click.option("--data", required=True, type=click.Path(exists=True))
@click.option(
    "--model",
    "model_name",
    default="elo",
    type=click.Choice(["elo", "logistic", "poisson", "gradient_boosting", "quantile", "ensemble"]),
)
@click.option("--min-train", default=20, show_default=True, type=int)
@click.option("--k-factor", default=20.0, show_default=True, type=float)
@click.option(
    "--no-mov",
    "use_mov",
    is_flag=True,
    default=True,
    flag_value=False,
)
@click.option("--output", type=click.Path(), default=None)
def calibrate(
    sport: str,
    data: str,
    model_name: str,
    min_train: int,
    k_factor: float,
    use_mov: bool,
    output: str | None,
) -> None:
    """Evaluate model calibration quality: Brier score, log-loss, and ECE."""
    games = CSVDataLoader().load(data)
    click.echo(f"Loaded {len(games)} games from {data}")

    model, extractor = _build_model_and_extractor(sport, model_name, k_factor, use_mov)

    pipeline = BacktestPipeline(
        model=model,
        extractor=extractor,
        detector=MinimumEdgeDetector(min_edge=0.0),
        sizer=KellySizer(fraction=0.25),
        bankroll=1000.0,
        min_train_games=min_train,
    )

    results = pipeline.run(games)
    if not results:
        click.echo("No predictions generated — try reducing --min-train or providing more data.")
        sys.exit(1)

    probs = [r.model_prob for r in results]
    outcomes = [1 if r.won else 0 for r in results]

    bs = brier_score(probs, outcomes)
    ll = log_loss(probs, outcomes)
    ece = expected_calibration_error(probs, outcomes)

    click.echo(f"\nCalibration report — {len(results)} predictions")
    click.echo(f"  Brier score : {bs:.4f}  (0 = perfect, 0.25 = random)")
    click.echo(f"  Log loss    : {ll:.4f}  (lower is better)")
    click.echo(f"  ECE         : {ece:.4f}  (0 = perfect calibration)")

    if output:
        report_dict = {"n_predictions": len(results), "brier_score": bs, "log_loss": ll, "ece": ece}
        try:
            with Path(output).open("w") as f:
                json.dump(report_dict, f, indent=2)
            click.echo(f"\nReport written to {output}")
        except OSError as exc:
            click.echo(f"Error writing report to {output}: {exc}", err=True)
            sys.exit(1)

    sys.exit(0)


@main.command(name="paper-trade")
@click.option(
    "--sport",
    required=True,
    type=click.Choice(_SPORT_CHOICES),
)
@click.option(
    "--host",
    default="http://localhost:8080",
    show_default=True,
    help="Base URL of the paper-trade Go service",
)
def paper_trade(sport: str, host: str) -> None:
    """Monitor the paper-trade service and display live performance."""
    import urllib.error
    import urllib.request

    parsed = urlparse(host)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ("localhost", "127.0.0.1"):
        click.echo(
            "Error: --host must be http://localhost:<port> or https://localhost:<port>",
            err=True,
        )
        sys.exit(1)

    perf_url = f"{host}/paper/performance"
    bets_url = f"{host}/paper/bets"

    try:
        with urllib.request.urlopen(perf_url) as resp:  # noqa: S310
            report = json.loads(resp.read())
        with urllib.request.urlopen(bets_url) as resp:  # noqa: S310
            bets = json.loads(resp.read())
    except urllib.error.URLError as exc:
        click.echo(f"Error connecting to paper-trade service at {host}: {exc}", err=True)
        sys.exit(1)

    click.echo(f"\nPaper trade performance ({sport})")
    click.echo(f"  Total bets  : {report.get('total_bets', 0)}")
    click.echo(f"  Won         : {report.get('won_bets', 0)}")
    click.echo(f"  Win rate    : {report.get('win_rate', 0):.1%}")
    click.echo(f"  Total staked: {report.get('total_staked', 0):.2f}")
    click.echo(f"  Profit      : {report.get('total_profit', 0):.2f}")
    click.echo(f"  ROI         : {report.get('roi', 0):.2%}")
    click.echo(f"\n  Open bets: {sum(1 for b in bets if b.get('Status') == 'open')}")


if __name__ == "__main__":
    main()
