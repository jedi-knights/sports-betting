"""HTTP client for the American Soccer Analysis (ASA) public API.

ASA provides free, unauthenticated access to soccer match results for several
US leagues including NWSL and MLS.  No API key is required.  Full docs:
https://app.americansocceranalysis.com/api/v1/__docs__/

This client uses only the stdlib (urllib) to avoid adding a dependency.

MLS pagination note: the API silently caps responses at 1,000 records per
request.  Since no single MLS season exceeds ~540 games, callers that need
complete multi-season histories should use ``get_mls_games(season_name=...)``
once per season.  See ``MLSDataFetcher`` for the recommended access pattern.
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
    """

    def __init__(self, base_url: str = _BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url) as resp:  # noqa: S310
            return json.loads(resp.read())

    def get_nwsl_games(self) -> list[dict[str, Any]]:
        """Fetch all available NWSL game results.

        Returns:
            List of raw game dicts from the ASA API.  Each dict contains at
            minimum ``game_id``, ``date_time_utc``, ``home_score``,
            ``away_score``, ``home_team_id``, ``away_team_id``.
        """
        return self._get("nwsl/games")

    def get_nwsl_teams(self) -> list[dict[str, Any]]:
        """Fetch the NWSL team reference table.

        Returns:
            List of raw team dicts.  Each dict contains at minimum
            ``team_id`` and ``team_name``.
        """
        return self._get("nwsl/teams")

    def get_mls_games(self, season_name: str | None = None) -> list[dict[str, Any]]:
        """Fetch MLS game results, optionally filtered to a single season.

        The ASA API silently caps responses at 1,000 records.  Pass
        ``season_name`` (e.g. ``"2024"``) to stay within the cap and retrieve
        a complete season; omit it only when a rough all-time sample is
        acceptable.

        Args:
            season_name: Four-digit season year, e.g. ``"2024"``.  When
                provided, the request adds ``status=FullTime`` to exclude
                in-progress fixtures from historical backtesting data.

        Returns:
            List of raw game dicts.  Each dict contains at minimum
            ``game_id``, ``date_time_utc``, ``home_score``, ``away_score``,
            ``home_team_id``, ``away_team_id``, ``season_name``.
        """
        params: dict[str, str] | None = None
        if season_name is not None:
            params = {"season_name": season_name, "status": "FullTime"}
        return self._get("mls/games", params=params)

    def get_mls_teams(self) -> list[dict[str, Any]]:
        """Fetch the MLS team reference table.

        Returns:
            List of raw team dicts.  Each dict contains at minimum
            ``team_id`` and ``team_name``.
        """
        return self._get("mls/teams")
