"""HTTP client for the Squadi sports management API.

Squadi (api.us.squadi.com) is the SaaS platform powering the WPSL schedule
and results pages.  The livescores endpoints are publicly accessible with no
authentication or API key.  A browser-style User-Agent header is required —
bare requests without it return an empty response body.

Full Squadi API documentation is not publicly available; the endpoints here
were discovered by inspecting network traffic on wpslsoccer.com.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

_BASE_URL = "https://api.us.squadi.com/livescores"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class SquadiClient:
    """Low-level client for the Squadi livescores API.

    All methods return raw decoded JSON as returned by the API.
    No domain transformation is performed here — see fetcher classes
    for typed output.
    """

    def __init__(self, base_url: str = _BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            return json.loads(resp.read())

    def get_competitions(self, org_key: str, year_ref_id: int) -> list[dict[str, Any]]:
        """Fetch all competitions for a Squadi organisation and year.

        Args:
            org_key: Organisation unique key (UUID string).
            year_ref_id: Squadi year reference ID (e.g. 6 = 2024, 7 = 2025).

        Returns:
            List of raw competition dicts.  Each dict contains at minimum
            ``id``, ``name``, and ``yearRefId``.
        """
        return self._get(
            "competitions/list",
            params={"organisationUniqueKey": org_key, "yearRefId": year_ref_id},
        )

    def get_matches(self, competition_id: int) -> list[dict[str, Any]]:
        """Fetch all matches for a competition as a flat list.

        The Squadi API returns matches nested inside round objects.  This
        method flattens that structure so callers receive a plain list of
        match dicts.

        Args:
            competition_id: Squadi competition ``id``.

        Returns:
            Flat list of raw match dicts.  Each dict contains at minimum
            ``id``, ``startTime``, ``matchStatus``, ``team1Score``,
            ``team2Score``, ``team1``, and ``team2``.
        """
        response = self._get("round/matches", params={"competitionId": competition_id})
        matches: list[dict[str, Any]] = []
        for round_ in response.get("rounds", []):
            matches.extend(round_.get("matches", []))
        return matches
