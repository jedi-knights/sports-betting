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

# Historical season IDs grouped by league.  Season IDs are not sequential
# across years — the gap varies as the platform added new leagues.  IDs were
# discovered by probing get-event-list-by-season-id back to 2015-16.
ECNL_GIRLS_SEASON_IDS: list[int] = [5, 6, 9, 12, 16, 23, 33, 41, 49, 60, 69]
ECNL_BOYS_SEASON_IDS: list[int] = [10, 13, 17, 24, 34, 42, 50, 61, 70]
ECRL_GIRLS_SEASON_IDS: list[int] = [15, 19, 26, 35, 43, 51, 62, 71]
ECRL_BOYS_SEASON_IDS: list[int] = [27, 36, 44, 52, 63, 72]

# All national + regional league seasons; excludes Pre-ECNL developmental tiers
ALL_ECNL_SEASON_IDS: list[int] = (
    ECNL_GIRLS_SEASON_IDS + ECNL_BOYS_SEASON_IDS + ECRL_GIRLS_SEASON_IDS + ECRL_BOYS_SEASON_IDS
)

# Default covers the current (2025-26) season only.  Fetching all history
# requires ~40 seasons × 10 conferences × 6 age groups of HTTP calls — callers
# that want full history should pass ALL_ECNL_SEASON_IDS explicitly.
_DEFAULT_SEASON_IDS = [69, 70, 71, 72]

# Maps AthleteOne season ID → sport slug used in HistoricalGame.sport.
_SEASON_SPORT_SLUGS: dict[int, str] = {
    **dict.fromkeys(ECNL_GIRLS_SEASON_IDS, "ecnl_girls"),
    **dict.fromkeys(ECNL_BOYS_SEASON_IDS, "ecnl_boys"),
    **dict.fromkeys(ECRL_GIRLS_SEASON_IDS, "ecrl_girls"),
    **dict.fromkeys(ECRL_BOYS_SEASON_IDS, "ecrl_boys"),
    # Pre-ECNL developmental leagues — included so unknown IDs get a correct slug
    # if passed explicitly, but excluded from ALL_ECNL_SEASON_IDS
    39: "pre_ecnl_girls",
    47: "pre_ecnl_girls",
    55: "pre_ecnl_girls",
    66: "pre_ecnl_girls",
    40: "pre_ecnl_boys",
    48: "pre_ecnl_boys",
    56: "pre_ecnl_boys",
    67: "pre_ecnl_boys",
}


class ECNLDataFetcher:
    """Fetch completed ECNL and ECRL match results from the AthleteOne API.

    Covers all four leagues sharing the AthleteOne platform at theecnl.com:
    ECNL Girls (season 69), ECNL Boys (70), ECRL Girls (71), ECRL Boys (72).

    Args:
        client: AthleteOneClient instance.  Defaults to a live client.  Pass
            a mock in tests.
        season_ids: List of AthleteOne season IDs to query.  Defaults to
            all four 2025-26 league seasons.  Pass a subset to restrict to
            specific leagues.
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
            sport_slug = _SEASON_SPORT_SLUGS.get(season_id, "ecnl")
            for event_id in self._get_event_ids(season_id):
                for flight_id in self._get_flight_ids(event_id):
                    for match in self._client.get_schedules_by_flight(event_id, flight_id):
                        if match.get("hometeamscore") is None or match.get("gameDate") is None:
                            continue
                        event_id_str = f"ecnl_{match['matchID']}"
                        if event_id_str in seen:
                            continue
                        seen.add(event_id_str)
                        games.append(self._to_game(match, event_id_str, sport_slug))

        return sorted(games, key=lambda g: g.game_date)

    def _get_event_ids(self, season_id: int) -> list[int]:
        if season_id not in self._event_ids_cache:
            self._event_ids_cache[season_id] = self._client.get_event_ids_for_season(season_id)
        return self._event_ids_cache[season_id]

    def _get_flight_ids(self, event_id: int) -> list[int]:
        if event_id not in self._flight_ids_cache:
            self._flight_ids_cache[event_id] = self._client.get_flight_ids_for_event(event_id)
        return self._flight_ids_cache[event_id]

    def _to_game(self, match: dict, event_id: str, sport_slug: str) -> HistoricalGame:
        game_date = datetime.strptime(match["gameDate"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
        return HistoricalGame(
            event_id=event_id,
            sport=sport_slug,
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
