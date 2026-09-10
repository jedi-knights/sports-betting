"""Run walk-forward MLS Poisson calibration and emit a markdown report.

Reads the MLS CSV, walks the pipeline once, and writes:
  - reports/mls_poisson_calibration.json  (metrics + reliability bins)
  - reports/mls_poisson_calibration.md    (human-readable summary)

Usage:
    uv run python scripts/mls_poisson_report.py [--data PATH] [--out-dir DIR] [--min-train N]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from bet.backtesting.loader import CSVDataLoader  # noqa: E402
from bet.backtesting.pipeline import BacktestPipeline  # noqa: E402
from bet.calibration.curve import calibration_curve  # noqa: E402
from bet.calibration.isotonic import IsotonicCalibrator  # noqa: E402
from bet.calibration.metrics import (  # noqa: E402
    brier_score,
    expected_calibration_error,
    log_loss,
)
from bet.calibration.model import CalibratedModel  # noqa: E402
from bet.features.mls import MLSFeatureExtractor  # noqa: E402
from bet.modeling.poisson import PoissonModel  # noqa: E402
from bet.sizing.kelly import KellySizer  # noqa: E402
from bet.value.detector import MinimumEdgeDetector  # noqa: E402


def _build_report(
    n_predictions: int,
    bs: float,
    ll: float,
    ece: float,
    curve_centers: list[float],
    curve_freqs: list[float],
    curve_counts: list[int],
    data_path: str,
    min_train: int,
) -> str:
    lines: list[str] = []
    lines.append("# MLS Poisson Calibration Report")
    lines.append("")
    lines.append(f"- **Data**: `{data_path}`")
    lines.append("- **Model**: Poisson (Dixon-Coles) wrapped in isotonic calibrator")
    lines.append(f"- **Predictions graded**: {n_predictions} (walk-forward, min_train={min_train})")
    lines.append("")
    lines.append("## Summary metrics")
    lines.append("")
    lines.append("| Metric | Value | Reference |")
    lines.append("|---|---:|---|")
    lines.append(f"| Brier score | {bs:.4f} | 0 = perfect, 0.25 = random coin flip |")
    lines.append(f"| Log loss | {ll:.4f} | Lower is better; unbounded above |")
    lines.append(f"| ECE | {ece:.4f} | 0 = perfectly calibrated |")
    lines.append("")
    lines.append("## Reliability diagram (home-win probability)")
    lines.append("")
    lines.append("Each row is a bin of predicted home-win probability.")
    lines.append("`observed` should track `predicted` for a well-calibrated model.")
    lines.append("")
    lines.append("| Predicted (bin center) | Observed frequency | Games in bin |")
    lines.append("|---:|---:|---:|")
    for c, f, n in zip(curve_centers, curve_freqs, curve_counts, strict=True):
        lines.append(f"| {c:.3f} | {f:.3f} | {n} |")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "A Brier score of 0.25 is the coin-flip baseline for a 3-way market when "
        "graded on home-win only. Values meaningfully below 0.25 indicate the model "
        "is extracting signal beyond the base rate."
    )
    lines.append("")
    lines.append(
        "ECE below 0.05 typically indicates the isotonic wrapper is doing its job. "
        "Larger values point at systematic over- or under-confidence in specific "
        "probability ranges — inspect the reliability table above to see which bins "
        "diverge from the diagonal."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        default=str(REPO_ROOT / "data" / "mls_full.csv"),
        help="Input CSV (default: data/mls_full.csv)",
    )
    parser.add_argument(
        "--out-dir",
        default=str(REPO_ROOT / "reports"),
        help="Output directory (default: reports/)",
    )
    parser.add_argument(
        "--min-train",
        type=int,
        default=100,
        help="Minimum training games before predicting (default: 100)",
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {data_path}...", flush=True)
    games = CSVDataLoader().load(str(data_path))
    print(f"  {len(games)} games loaded", flush=True)

    model = CalibratedModel(PoissonModel(), IsotonicCalibrator())
    pipeline = BacktestPipeline(
        model=model,
        extractor=MLSFeatureExtractor(),
        detector=MinimumEdgeDetector(min_edge=0.0),
        sizer=KellySizer(fraction=0.25),
        bankroll=1000.0,
        min_train_games=args.min_train,
    )

    print(f"Walking pipeline (min_train={args.min_train})...", flush=True)
    probs: list[float] = []
    outcomes: list[int] = []
    for i, (game, estimate) in enumerate(pipeline.predictions(games), start=1):
        probs.append(estimate.home_win)
        outcomes.append(1 if game.home_score > game.away_score else 0)
        if i % 250 == 0:
            print(f"  graded {i} predictions...", flush=True)

    if not probs:
        print("ERROR: no predictions produced", file=sys.stderr)
        return 1

    bs = brier_score(probs, outcomes)
    ll = log_loss(probs, outcomes)
    ece = expected_calibration_error(probs, outcomes)
    curve = calibration_curve(probs, outcomes, n_bins=10)

    report_json = {
        "n_predictions": len(probs),
        "brier_score": bs,
        "log_loss": ll,
        "ece": ece,
        "min_train": args.min_train,
        "reliability_bins": [
            {"predicted": c, "observed": f, "count": n}
            for c, f, n in zip(
                curve.bin_centers, curve.observed_frequencies, curve.bin_counts, strict=True
            )
        ],
    }

    json_path = out_dir / "mls_poisson_calibration.json"
    md_path = out_dir / "mls_poisson_calibration.md"

    with json_path.open("w") as f:
        json.dump(report_json, f, indent=2)

    md = _build_report(
        n_predictions=len(probs),
        bs=bs,
        ll=ll,
        ece=ece,
        curve_centers=curve.bin_centers,
        curve_freqs=curve.observed_frequencies,
        curve_counts=curve.bin_counts,
        data_path=str(data_path.relative_to(REPO_ROOT)),
        min_train=args.min_train,
    )
    md_path.write_text(md)

    print("")
    print(f"Predictions : {len(probs)}")
    print(f"Brier score : {bs:.4f}")
    print(f"Log loss    : {ll:.4f}")
    print(f"ECE         : {ece:.4f}")
    print("")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
