"""HTTP client for the AthleteOne / TotalGlobalSports sports data API.

AthleteOne (api.athleteone.com) powers ECNL schedule and standings widgets
embedded in the Sidearm Sports CMS pages at theecnl.com.  The API is publicly
accessible with no authentication, but requires:
  - A browser-style User-Agent header (bare requests return "Disallowed client")
  - An Origin header matching theecnl.com (CORS enforcement)

The /api/Event/ endpoints return JSON.  The /api/Script/ endpoints return HTML
fragments used by the embedded Angular widgets; only the event-list endpoint
is used here since no JSON equivalent exists for season-to-event discovery.
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

_BASE_URL = "https://api.athleteone.com/api"
_ORIGIN = "https://theecnl.com"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class AthleteOneClient:
    """Low-level client for the AthleteOne REST API.

    All methods return raw decoded data as returned by the API.  No domain
    transformation is performed here — see ECNLDataFetcher for typed output.
    """

    def __init__(self, base_url: str = _BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def _request(self, path: str) -> bytes:
        url = f"{self._base_url}/{path.lstrip('/')}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": _USER_AGENT, "Origin": _ORIGIN},
        )
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            return resp.read()

    def get_event_ids_for_season(self, season_id: int) -> list[int]:
        """Return all event IDs for a Squadi season.

        Uses the Script HTML endpoint (no JSON equivalent exists) and parses
        the <option value="..."> tags to extract event IDs.  The placeholder
        option (value="0") is excluded.

        Args:
            season_id: AthleteOne season ID (e.g. 69 = 2025-26).

        Returns:
            List of integer event IDs for the season.
        """
        html = self._request(f"Script/get-event-list-by-season-id/{season_id}/0").decode()
        return [int(v) for v in re.findall(r'value="(\d+)"', html) if v != "0"]

    def get_flight_ids_for_event(self, event_id: int) -> list[int]:
        """Return all flight IDs for an event.

        An event is a conference (e.g. "ECNL Girls Mid-Atlantic 2025-26").
        Each flight corresponds to one age group within that conference.

        Args:
            event_id: AthleteOne event ID.

        Returns:
            List of integer flight IDs covering both girls and boys divisions.
        """
        raw = json.loads(self._request(f"Event/get-event-schedule-or-standings/{event_id}"))
        flight_ids: list[int] = []
        data = raw.get("data", {})
        for list_key in ("girlsDivAndFlightList", "boysDivAndFlightList"):
            for division in data.get(list_key, []):
                for flight in division.get("flightList", []):
                    flight_ids.append(flight["flightID"])
        return flight_ids

    def get_schedules_by_flight(self, event_id: int, flight_id: int) -> list[dict[str, Any]]:
        """Return all matches for a conference age-group flight.

        Args:
            event_id: AthleteOne event ID (conference).
            flight_id: AthleteOne flight ID (age group within the conference).

        Returns:
            List of raw match dicts.  Each dict contains at minimum
            ``matchID``, ``gameDate``, ``homeTeam``, ``awayTeam``,
            ``hometeamscore``, and ``awayteamscore``.  Score fields are
            ``None`` for scheduled (not yet played) matches.
        """
        raw = json.loads(self._request(f"Event/get-schedules-by-flight/{event_id}/{flight_id}/0"))
        if isinstance(raw, list):
            return raw
        return raw.get("data", [])
