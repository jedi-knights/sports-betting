"""Fetch NFL historical game data and convert to backtest CSV format.

Requires nfl-data-py (dev dependency). Usage:
    uv run python scripts/fetch_nfl_data.py --season 2023 --output data/nfl_2023.csv

Output columns match the CSVDataLoader schema:
    event_id, sport, home_team, away_team, game_date,
    home_score, away_score, home_win_odds, away_win_odds, draw_odds,
    closing_home_win_odds, closing_away_win_odds, closing_draw_odds

Odds source: nfl-data-py moneylines (American → decimal conversion).
Closing odds: synthetic — opening implied probabilities shifted by ±3% to
simulate typical line movement. The shift direction is seeded for reproducibility
but is not derived from actual closing lines; treat CLV results as indicative only.
"""

from __future__ import annotations

import argparse
import csv
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")  # suppress nfl-data-py verbose output


def american_to_decimal(american: float) -> float:
    """Convert American moneyline odds to decimal odds."""
    if american >= 0:
        return american / 100.0 + 1.0
    return 100.0 / abs(american) + 1.0


def synthetic_closing_odds(
    home_ml: float,
    away_ml: float,
    rng: np.random.Generator,
    shift_scale: float = 0.03,
) -> tuple[float, float]:
    """Derive synthetic closing odds by applying a random probability shift.

    A uniform shift in implied probability is applied to both sides in opposite
    directions, simulating typical line movement. The vig ratio is preserved.
    """
    home_dec = american_to_decimal(home_ml)
    away_dec = american_to_decimal(away_ml)
    home_raw_prob = 1.0 / home_dec
    away_raw_prob = 1.0 / away_dec
    # Overround factor (sum of raw implied probs > 1)
    overround = home_raw_prob + away_raw_prob

    # Shift home implied probability; adjust away to maintain overround
    shift = rng.uniform(-shift_scale, shift_scale)
    home_new = np.clip(home_raw_prob + shift, 0.05, overround - 0.05)
    away_new = overround - home_new

    return 1.0 / home_new, 1.0 / away_new


def fetch(season: int, output: Path) -> int:
    try:
        import nfl_data_py as nfl  # noqa: PLC0415
    except ImportError:
        print("ERROR: nfl-data-py not installed. Run: uv sync", file=sys.stderr)
        return 1

    sched = nfl.import_schedules([season])
    reg = sched[sched["game_type"] == "REG"].copy()
    # Drop games without final scores (bye weeks or future games)
    required = ["home_score", "away_score", "home_moneyline", "away_moneyline"]
    reg = reg.dropna(subset=required)
    reg = reg.sort_values("gameday").reset_index(drop=True)

    rng = np.random.default_rng(42)
    output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "event_id",
        "sport",
        "home_team",
        "away_team",
        "game_date",
        "home_score",
        "away_score",
        "home_win_odds",
        "away_win_odds",
        "draw_odds",
        "closing_home_win_odds",
        "closing_away_win_odds",
        "closing_draw_odds",
    ]

    rows_written = 0
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for _, row in reg.iterrows():
            home_ml = float(row["home_moneyline"])
            away_ml = float(row["away_moneyline"])
            home_dec = american_to_decimal(home_ml)
            away_dec = american_to_decimal(away_ml)
            closing_home, closing_away = synthetic_closing_odds(home_ml, away_ml, rng)

            # Combine date + time; treat as UTC (games are ET, ±5h offset is
            # immaterial for walk-forward ordering within a season)
            gametime = str(row.get("gametime", "12:00") or "12:00")
            game_date = f"{row['gameday']}T{gametime}:00+00:00"

            writer.writerow(
                {
                    "event_id": row["game_id"],
                    "sport": "nfl",
                    "home_team": row["home_team"],
                    "away_team": row["away_team"],
                    "game_date": game_date,
                    "home_score": int(row["home_score"]),
                    "away_score": int(row["away_score"]),
                    "home_win_odds": f"{home_dec:.4f}",
                    "away_win_odds": f"{away_dec:.4f}",
                    "draw_odds": "",
                    "closing_home_win_odds": f"{closing_home:.4f}",
                    "closing_away_win_odds": f"{closing_away:.4f}",
                    "closing_draw_odds": "",
                }
            )
            rows_written += 1

    print(f"Wrote {rows_written} games to {output}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=2023)
    parser.add_argument("--output", type=Path, default=Path("data/nfl_2023.csv"))
    args = parser.parse_args()
    sys.exit(fetch(args.season, args.output))


if __name__ == "__main__":
    main()
