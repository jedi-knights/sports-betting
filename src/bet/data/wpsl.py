"""Data fetcher for WPSL match results via the Squadi livescores API.

WPSL (Women's Premier Soccer League) uses Squadi as its schedule/results
platform.  Squadi is publicly accessible with no authentication.  The WPSL
organisation key is a stable UUID that identifies the league within Squadi.

Only the main WPSL competition is fetched — U21 and Division II competitions
are excluded because the model is trained only on the top division.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..backtesting.types import HistoricalGame
from .squadi import SquadiClient

_WPSL_ORG_KEY = "4257ebc9-d65f-422c-a3b5-45c6e42038d5"
_DEFAULT_YEAR_REF_IDS = [6, 7]  # 6 = 2024, 7 = 2025


def _is_main_wpsl(name: str) -> bool:
    upper = name.upper()
    return "WPSL" in upper and "U21" not in upper and "DIVISION" not in upper


class WPSLDataFetcher:
    """Fetch completed WPSL match results from the Squadi livescores API.

    Args:
        client: SquadiClient instance.  Defaults to a live client.  Pass a
            mock in tests.
        year_ref_ids: List of Squadi year reference IDs to query.  Defaults
            to ``[6, 7]`` (2024 and 2025).
    """

    def __init__(
        self,
        client: SquadiClient | None = None,
        year_ref_ids: list[int] | None = None,
    ) -> None:
        self._client = client or SquadiClient()
        self._year_ref_ids = year_ref_ids if year_ref_ids is not None else _DEFAULT_YEAR_REF_IDS

    def fetch(self) -> list[HistoricalGame]:
        """Fetch completed WPSL match results.

        Returns:
            List of HistoricalGame objects sorted by game_date ascending.
            Duplicate match IDs across competitions or years are deduplicated.
            All odds fields are None (Squadi provides no odds data).
        """
        seen: set[str] = set()
        games: list[HistoricalGame] = []

        for year_ref_id in self._year_ref_ids:
            competitions = self._client.get_competitions(_WPSL_ORG_KEY, year_ref_id)
            for comp in competitions:
                if not _is_main_wpsl(comp.get("name", "")):
                    continue
                for match in self._client.get_matches(competition_id=comp["id"]):
                    if match.get("matchStatus") != "ENDED":
                        continue
                    event_id = f"wpsl_{match['id']}"
                    if event_id in seen:
                        continue
                    seen.add(event_id)
                    games.append(self._to_game(match, event_id))

        return sorted(games, key=lambda g: g.game_date)

    def _to_game(self, match: dict, event_id: str) -> HistoricalGame:
        game_date = datetime.strptime(match["startTime"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=UTC
        )
        return HistoricalGame(
            event_id=event_id,
            sport="wpsl",
            home_team=match["team1"]["name"],
            away_team=match["team2"]["name"],
            game_date=game_date,
            home_score=int(match["team1Score"]),
            away_score=int(match["team2Score"]),
            home_win_odds=None,
            away_win_odds=None,
            draw_odds=None,
            closing_home_win_odds=None,
            closing_away_win_odds=None,
            closing_draw_odds=None,
        )
