"""HTTP client for the American Soccer Analysis (ASA) public API.

ASA provides free, unauthenticated access to soccer match results for several
US leagues including the NWSL.  No API key is required.  Full documentation:
https://app.americansocceranalysis.com/api/v1/__docs__/

This client uses only the stdlib (urllib) to avoid adding a dependency.
"""

from __future__ import annotations

import json
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

    def _get(self, path: str) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
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
