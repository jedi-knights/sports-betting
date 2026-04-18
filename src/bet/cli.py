"""Entry point for the bet CLI."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict

import click

from .backtesting.loader import CSVDataLoader
from .backtesting.pipeline import BacktestPipeline
from .features.nfl import NFLFeatureExtractor
from .features.soccer import SoccerFeatureExtractor
from .modeling.elo import EloModel
from .modeling.logistic import LogisticRegressionModel
from .modeling.poisson import PoissonModel
from .sizing.kelly import KellySizer
from .tracking.metrics import compute_performance_report
from .value.detector import MinimumEdgeDetector


@click.group()
def main() -> None:
    """Sports betting modeling and backtesting CLI."""


@main.command()
@click.option("--sport", required=True, type=click.Choice(["nfl", "soccer"]))
@click.option("--data", required=True, type=click.Path(exists=True))
@click.option(
    "--model",
    "model_name",
    default="elo",
    type=click.Choice(["elo", "logistic", "poisson"]),
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
) -> None:
    """Run walk-forward backtesting on historical game data."""
    games = CSVDataLoader().load(data)
    click.echo(f"Loaded {len(games)} games from {data}")

    if sport == "nfl" and model_name == "logistic":
        model = LogisticRegressionModel()
        extractor = NFLFeatureExtractor(k_factor=k_factor, use_mov=use_mov)
    elif sport == "nfl":
        model = EloModel(k_factor=k_factor, use_mov=use_mov)
        extractor = NFLFeatureExtractor(k_factor=k_factor, use_mov=use_mov)
    else:
        model = PoissonModel()
        extractor = SoccerFeatureExtractor()

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

    if output:
        report_dict = asdict(report)
        with open(output, "w") as f:
            json.dump(report_dict, f, indent=2)
        click.echo(f"\nReport written to {output}")

    sys.exit(0)


@main.command(name="paper-trade")
@click.option("--sport", required=True, type=click.Choice(["nfl", "soccer"]))
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

    perf_url = f"{host}/paper/performance"
    bets_url = f"{host}/paper/bets"

    try:
        with urllib.request.urlopen(perf_url) as resp:  # noqa: S310
            report = json.loads(resp.read())
        with urllib.request.urlopen(bets_url) as resp:  # noqa: S310
            bets = json.loads(resp.read())
    except urllib.error.URLError as exc:
        click.echo(
            f"Error connecting to paper-trade service at {host}: {exc}", err=True
        )
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
