"""MLS historical game data fetcher backed by the American Soccer Analysis API.

The ASA API is free and unauthenticated.  Its response is silently capped at
1,000 records, so pass ``seasons`` when collecting complete multi-season
histories (each MLS season has up to ~540 games, well within the cap).

Odds are unavailable from ASA — all odds fields on the returned HistoricalGame
objects are None.

Usage::

    from bet.data.mls import MLSDataFetcher

    # Specific seasons — recommended for complete histories
    fetcher = MLSDataFetcher(seasons=["2022", "2023", "2024"])
    games = fetcher.fetch()
"""

from __future__ import annotations

from .base import ASALeagueDataFetcher


class MLSDataFetcher(ASALeagueDataFetcher):
    """Fetches MLS game results from the American Soccer Analysis API."""

    league_slug = "mls"
    sport_slug = "mls"
