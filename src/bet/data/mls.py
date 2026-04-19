"""MLS historical game data fetcher backed by the American Soccer Analysis API.

The ASA API is free and unauthenticated.  It silently caps responses at 1,000
records, so this fetcher accepts an optional ``seasons`` list and issues one
request per season to guarantee complete data.  No single MLS season exceeds
~540 games, well within the cap.

Odds are not available from ASA.  All odds fields on the returned
HistoricalGame objects are set to None.  The BacktestPipeline treats such
games as training-only — they inform the Poisson model but produce no bets.

Usage::

    from bet.data.mls import MLSDataFetcher

    # All available seasons (may hit the 1,000-record cap)
    fetcher = MLSDataFetcher()
    games = fetcher.fetch()

    # Specific seasons — recommended for complete histories
    fetcher = MLSDataFetcher(seasons=["2022", "2023", "2024"])
    games = fetcher.fetch()
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..backtesting.types import HistoricalGame
from .asa import ASAClient


class MLSDataFetcher:
    """Adapter that fetches MLS results from the ASA API and returns
    HistoricalGame objects consumable by the existing backtesting pipeline.

    Args:
        client: ASAClient instance.  Defaults to a new client pointing at the
            live ASA API.  Pass a mock in tests.
        seasons: Optional list of four-digit season years (e.g.
            ``["2022", "2023", "2024"]``).  When provided, one API call is
            made per season to avoid the 1,000-record response cap.  When
            omitted, a single call fetches all available data.
    """

    def __init__(
        self,
        client: ASAClient | None = None,
        seasons: list[str] | None = None,
    ) -> None:
        self._client = client or ASAClient()
        self._seasons = seasons

    def fetch(self) -> list[HistoricalGame]:
        """Fetch MLS game results from the ASA API.

        Returns:
            List of HistoricalGame objects sorted by game_date ascending.
            Duplicate game IDs (possible when seasons overlap) are removed.
            All odds fields are None (ASA provides no odds data).
        """
        teams_raw = self._client.get_mls_teams()
        team_names: dict[str, str] = {t["team_id"]: t["team_name"] for t in teams_raw}

        if self._seasons:
            raw_games: list[dict[str, Any]] = []
            for season in self._seasons:
                raw_games.extend(self._client.get_mls_games(season_name=season))
        else:
            raw_games = self._client.get_mls_games()

        seen: set[str] = set()
        games: list[HistoricalGame] = []
        for raw in raw_games:
            gid = raw["game_id"]
            if gid in seen:
                continue
            seen.add(gid)
            games.append(self._to_game(raw, team_names))

        return sorted(games, key=lambda g: g.game_date)

    @staticmethod
    def _to_game(raw: dict[str, Any], team_names: dict[str, str]) -> HistoricalGame:
        home_id = raw["home_team_id"]
        away_id = raw["away_team_id"]
        game_date = datetime.strptime(raw["date_time_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        return HistoricalGame(
            event_id=raw["game_id"],
            sport="mls",
            home_team=team_names.get(home_id, home_id),
            away_team=team_names.get(away_id, away_id),
            game_date=game_date,
            home_score=int(raw["home_score"]),
            away_score=int(raw["away_score"]),
            home_win_odds=None,
            away_win_odds=None,
            draw_odds=None,
            closing_home_win_odds=None,
            closing_away_win_odds=None,
            closing_draw_odds=None,
        )
