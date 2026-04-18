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
    "--model", "model_name", default="elo", type=click.Choice(["elo", "poisson"])
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
@click.option("--output", type=click.Path(), default=None)
def backtest(
    sport: str,
    data: str,
    model_name: str,
    min_edge: float,
    bankroll: float,
    kelly_fraction: float,
    min_train: int,
    output: str | None,
) -> None:
    """Run walk-forward backtesting on historical game data."""
    games = CSVDataLoader().load(data)
    click.echo(f"Loaded {len(games)} games from {data}")

    if model_name == "elo":
        model = EloModel()
        extractor = NFLFeatureExtractor()
    else:
        model = PoissonModel()
        extractor = SoccerFeatureExtractor()

    pipeline = BacktestPipeline(
        model=model,
        extractor=extractor,
        detector=MinimumEdgeDetector(min_edge=min_edge),
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


if __name__ == "__main__":
    main()
