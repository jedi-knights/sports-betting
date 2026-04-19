"""NWSL historical game data fetcher backed by the American Soccer Analysis API.

The ASA API returns game results (scores, dates, team IDs) but no odds data.
All odds fields on the returned HistoricalGame objects are set to None.  The
BacktestPipeline treats games with None odds as training-only — they build the
Poisson strength model but produce no value bets, since there is no market line
to bet against.

Usage::

    from bet.data.nwsl import NWSLDataFetcher

    fetcher = NWSLDataFetcher()
    games = fetcher.fetch()  # list[HistoricalGame]
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..backtesting.types import HistoricalGame
from .asa import ASAClient


class NWSLDataFetcher:
    """Adapter that fetches NWSL results from the ASA API and returns
    HistoricalGame objects consumable by the existing backtesting pipeline.

    Args:
        client: ASAClient instance.  Defaults to a new client pointing at the
            live ASA API.  Pass a mock in tests.
    """

    def __init__(self, client: ASAClient | None = None) -> None:
        self._client = client or ASAClient()

    def fetch(self) -> list[HistoricalGame]:
        """Fetch all available NWSL game results from the ASA API.

        Returns:
            List of HistoricalGame objects sorted by game_date ascending.
            All odds fields are None (ASA provides no odds data).
        """
        teams_raw = self._client.get_nwsl_teams()
        team_names: dict[str, str] = {t["team_id"]: t["team_name"] for t in teams_raw}

        games_raw = self._client.get_nwsl_games()
        games = [self._to_game(g, team_names) for g in games_raw]
        return sorted(games, key=lambda g: g.game_date)

    @staticmethod
    def _to_game(raw: dict[str, Any], team_names: dict[str, str]) -> HistoricalGame:
        home_id = raw["home_team_id"]
        away_id = raw["away_team_id"]
        game_date = datetime.strptime(raw["date_time_utc"], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=UTC
        )
        return HistoricalGame(
            event_id=raw["game_id"],
            sport="nwsl",
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
