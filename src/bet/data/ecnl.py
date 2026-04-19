"""Data fetcher for ECNL match results via the AthleteOne API.

ECNL (Elite Clubs National League) uses AthleteOne / TotalGlobalSports as its
schedule platform, embedded in Sidearm Sports pages at theecnl.com.

Fetching all matches for a season requires three layers of ID resolution:
  season_id → event_ids (one per conference)
              → flight_ids (one per age group)
                → matches (full schedule with scores)

The event_ids and flight_ids layers are stable within a season and are cached
on the fetcher instance so that repeated fetch() calls do not re-request them.
Match data is always fetched fresh.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..backtesting.types import HistoricalGame
from .athleteone import AthleteOneClient

_DEFAULT_SEASON_IDS = [69]  # 69 = 2025-26


class ECNLDataFetcher:
    """Fetch completed ECNL match results from the AthleteOne API.

    Args:
        client: AthleteOneClient instance.  Defaults to a live client.  Pass
            a mock in tests.
        season_ids: List of AthleteOne season IDs to query.  Defaults to
            ``[69]`` (2025-26).  Season IDs are sequential integers; 69 is the
            most recent confirmed season.
    """

    def __init__(
        self,
        client: AthleteOneClient | None = None,
        season_ids: list[int] | None = None,
    ) -> None:
        self._client = client or AthleteOneClient()
        self._season_ids = season_ids if season_ids is not None else _DEFAULT_SEASON_IDS
        self._event_ids_cache: dict[int, list[int]] = {}
        self._flight_ids_cache: dict[int, list[int]] = {}

    def fetch(self) -> list[HistoricalGame]:
        """Fetch completed ECNL match results.

        Returns:
            List of HistoricalGame objects sorted by game_date ascending.
            Duplicate match IDs across flights or seasons are deduplicated.
            All odds fields are None (AthleteOne provides no odds data).
        """
        seen: set[str] = set()
        games: list[HistoricalGame] = []

        for season_id in self._season_ids:
            for event_id in self._get_event_ids(season_id):
                for flight_id in self._get_flight_ids(event_id):
                    for match in self._client.get_schedules_by_flight(event_id, flight_id):
                        if match.get("hometeamscore") is None:
                            continue
                        event_id_str = f"ecnl_{match['matchID']}"
                        if event_id_str in seen:
                            continue
                        seen.add(event_id_str)
                        games.append(self._to_game(match, event_id_str))

        return sorted(games, key=lambda g: g.game_date)

    def _get_event_ids(self, season_id: int) -> list[int]:
        if season_id not in self._event_ids_cache:
            self._event_ids_cache[season_id] = self._client.get_event_ids_for_season(season_id)
        return self._event_ids_cache[season_id]

    def _get_flight_ids(self, event_id: int) -> list[int]:
        if event_id not in self._flight_ids_cache:
            self._flight_ids_cache[event_id] = self._client.get_flight_ids_for_event(event_id)
        return self._flight_ids_cache[event_id]

    def _to_game(self, match: dict, event_id: str) -> HistoricalGame:
        game_date = datetime.strptime(match["gameDate"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
        return HistoricalGame(
            event_id=event_id,
            sport="ecnl",
            home_team=match["homeTeam"],
            away_team=match["awayTeam"],
            game_date=game_date,
            home_score=int(match["hometeamscore"]),
            away_score=int(match["awayteamscore"]),
            home_win_odds=None,
            away_win_odds=None,
            draw_odds=None,
            closing_home_win_odds=None,
            closing_away_win_odds=None,
            closing_draw_odds=None,
        )
