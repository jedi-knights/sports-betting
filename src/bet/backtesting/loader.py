"""Historical game data loader."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from .types import HistoricalGame


class CSVDataLoader:
    """Loads historical games from a CSV file.

    Expected column order (header row required):
    event_id, sport, home_team, away_team, game_date,
    home_score, away_score, home_win_odds, away_win_odds, draw_odds,
    closing_home_win_odds, closing_away_win_odds, closing_draw_odds

    ``draw_odds`` and ``closing_draw_odds`` may be empty strings for binary
    sports (NFL, NBA); they are stored as ``None`` in that case.
    """

    def load(self, path: str) -> list[HistoricalGame]:
        """Load games from a CSV file at the given path.

        Args:
            path: Filesystem path to the CSV file.

        Returns:
            List of HistoricalGame objects in file order.
        """
        games: list[HistoricalGame] = []
        with Path(path).open(newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=1):
                try:
                    games.append(self._parse_row(row))
                except (ValueError, KeyError) as exc:
                    raise ValueError(f"row {idx}: {exc}") from exc
        return games

    @staticmethod
    def _parse_row(row: dict[str, str]) -> HistoricalGame:
        def _float_or_none(val: str) -> float | None:
            stripped = val.strip()
            return float(stripped) if stripped else None

        game_date = datetime.fromisoformat(row["game_date"].strip())
        if game_date.tzinfo is None:
            game_date = game_date.replace(tzinfo=UTC)

        return HistoricalGame(
            event_id=row["event_id"].strip(),
            sport=row["sport"].strip(),
            home_team=row["home_team"].strip(),
            away_team=row["away_team"].strip(),
            game_date=game_date,
            home_score=int(row["home_score"]),
            away_score=int(row["away_score"]),
            home_win_odds=float(row["home_win_odds"]),
            away_win_odds=float(row["away_win_odds"]),
            draw_odds=_float_or_none(row["draw_odds"]),
            closing_home_win_odds=float(row["closing_home_win_odds"]),
            closing_away_win_odds=float(row["closing_away_win_odds"]),
            closing_draw_odds=_float_or_none(row["closing_draw_odds"]),
            temperature=_float_or_none(row.get("temperature", "")),
            wind_mph=_float_or_none(row.get("wind_mph", "")),
            precipitation=row.get("precipitation", "").strip().lower() in ("true", "1", "yes"),
        )
