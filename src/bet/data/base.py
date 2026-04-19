"""Base fetcher for ASA-backed soccer league data.

All league fetchers (NWSL, MLS, USL Super League, etc.) share the same
fetch logic: resolve team IDs from the teams endpoint, pull games one
season at a time to avoid the API's 1,000-record response cap, deduplicate
on ``game_id``, and return a sorted ``list[HistoricalGame]``.

Each concrete fetcher is a three-line subclass that sets ``league_slug``
(the ASA API path segment) and ``sport_slug`` (the value written into
``HistoricalGame.sport``, which must match the CLI extractor slug).

Example::

    class NWSLDataFetcher(ASALeagueDataFetcher):
        league_slug = "nwsl"
        sport_slug = "nwsl"
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from ..backtesting.types import HistoricalGame
from .asa import ASAClient


class ASALeagueDataFetcher:
    """Shared fetch logic for all ASA-backed soccer league data adapters.

    Subclasses must set ``league_slug`` and ``sport_slug`` as class
    attributes.  Everything else is inherited.

    Args:
        client: ASAClient instance.  Defaults to a live client.  Pass a
            mock in tests.
        seasons: Optional list of season identifiers (e.g.
            ``["2022", "2023", "2024"]``).  When provided, one API call is
            issued per season to stay within the 1,000-record response cap.
            When omitted, a single call fetches all available data.
    """

    league_slug: ClassVar[str]
    sport_slug: ClassVar[str]

    def __init__(
        self,
        client: ASAClient | None = None,
        seasons: list[str] | None = None,
    ) -> None:
        self._client = client or ASAClient()
        self._seasons = seasons

    def fetch(self) -> list[HistoricalGame]:
        """Fetch completed game results from the ASA API.

        Returns:
            List of HistoricalGame objects sorted by game_date ascending.
            Duplicate game IDs across season queries are deduplicated.
            All odds fields are None (ASA provides no odds data).
        """
        teams_raw = self._client.get_league_teams(self.league_slug)
        team_names: dict[str, str] = {t["team_id"]: t["team_name"] for t in teams_raw}

        if self._seasons:
            raw_games: list[dict[str, Any]] = []
            for season in self._seasons:
                raw_games.extend(
                    self._client.get_league_games(self.league_slug, season_name=season)
                )
        else:
            raw_games = self._client.get_league_games(self.league_slug)

        seen: set[str] = set()
        games: list[HistoricalGame] = []
        for raw in raw_games:
            gid = raw["game_id"]
            if gid in seen:
                continue
            seen.add(gid)
            games.append(self._to_game(raw, team_names))

        return sorted(games, key=lambda g: g.game_date)

    def _to_game(self, raw: dict[str, Any], team_names: dict[str, str]) -> HistoricalGame:
        home_id = raw["home_team_id"]
        away_id = raw["away_team_id"]
        date_str = raw["date_time_utc"].removesuffix(" UTC")
        game_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        return HistoricalGame(
            event_id=raw["game_id"],
            sport=self.sport_slug,
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
