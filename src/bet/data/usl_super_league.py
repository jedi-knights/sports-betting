"""USL Super League historical game data fetcher backed by the American Soccer Analysis API.

The ASA API covers the USL Super League under the slug ``usls``, starting
with the inaugural 2024-25 season.  The API is free and unauthenticated.
Odds are unavailable — all odds fields on the returned HistoricalGame objects
are None.

Usage::

    from bet.data.usl_super_league import USLSuperLeagueDataFetcher

    fetcher = USLSuperLeagueDataFetcher()
    games = fetcher.fetch()  # list[HistoricalGame]

    # Season-by-season (recommended once more seasons accumulate)
    fetcher = USLSuperLeagueDataFetcher(seasons=["2024-25", "2025-26"])
    games = fetcher.fetch()
"""

from __future__ import annotations

from .base import ASALeagueDataFetcher


class USLSuperLeagueDataFetcher(ASALeagueDataFetcher):
    """Fetches USL Super League game results from the American Soccer Analysis API."""

    league_slug = "usls"
    sport_slug = "usl_super_league"
