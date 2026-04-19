"""HTTP client for the American Soccer Analysis (ASA) public API.

ASA provides free, unauthenticated access to soccer match results for several
US leagues including NWSL, MLS, and USL Super League.  No API key is required.
Full docs: https://app.americansocceranalysis.com/api/v1/__docs__/

This client uses only the stdlib (urllib) to avoid adding a dependency.

Pagination note: the API silently caps responses at 1,000 records per request.
Since no single season exceeds ~540 games, callers that need complete
multi-season histories should use ``get_league_games(league, season_name=...)``
once per season.  See ``ASALeagueDataFetcher`` for the recommended pattern.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

_BASE_URL = "https://app.americansocceranalysis.com/api/v1"


class ASAClient:
    """Low-level client for the American Soccer Analysis REST API.

    All methods return raw decoded JSON (list of dicts) as returned by the
    API.  No transformation is performed here; see the fetcher layer for
    domain-typed output.

    The generic ``get_league_games`` / ``get_league_teams`` methods accept any
    league slug recognised by the ASA API (e.g. ``"nwsl"``, ``"mls"``,
    ``"usls"``).  League-specific wrappers are kept for backward compatibility
    but delegate to the generic methods.
    """

    def __init__(self, base_url: str = _BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url) as resp:  # noqa: S310
            return json.loads(resp.read())

    # ------------------------------------------------------------------
    # Generic league-agnostic interface
    # ------------------------------------------------------------------

    def get_league_games(self, league: str, season_name: str | None = None) -> list[dict[str, Any]]:
        """Fetch game results for any ASA-supported league.

        Args:
            league: ASA API path segment, e.g. ``"nwsl"``, ``"mls"``,
                ``"usls"``.
            season_name: Season identifier, e.g. ``"2024"`` or ``"2024-25"``.
                When provided, the request adds ``status=FullTime`` to exclude
                in-progress fixtures from historical backtesting data.

        Returns:
            List of raw game dicts containing at minimum ``game_id``,
            ``date_time_utc``, ``home_score``, ``away_score``,
            ``home_team_id``, ``away_team_id``.
        """
        params: dict[str, str] | None = None
        if season_name is not None:
            params = {"season_name": season_name, "status": "FullTime"}
        return self._get(f"{league}/games", params=params)

    def get_league_teams(self, league: str) -> list[dict[str, Any]]:
        """Fetch the team reference table for any ASA-supported league.

        Args:
            league: ASA API path segment, e.g. ``"nwsl"``, ``"mls"``,
                ``"usls"``.

        Returns:
            List of raw team dicts containing at minimum ``team_id`` and
            ``team_name``.
        """
        return self._get(f"{league}/teams")

    # ------------------------------------------------------------------
    # League-specific wrappers — kept for backward compatibility
    # ------------------------------------------------------------------

    def get_nwsl_games(self) -> list[dict[str, Any]]:
        """Fetch all available NWSL game results."""
        return self.get_league_games("nwsl")

    def get_nwsl_teams(self) -> list[dict[str, Any]]:
        """Fetch the NWSL team reference table."""
        return self.get_league_teams("nwsl")

    def get_mls_games(self, season_name: str | None = None) -> list[dict[str, Any]]:
        """Fetch MLS game results, optionally filtered to a single season."""
        return self.get_league_games("mls", season_name=season_name)

    def get_mls_teams(self) -> list[dict[str, Any]]:
        """Fetch the MLS team reference table."""
        return self.get_league_teams("mls")
