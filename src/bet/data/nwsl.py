"""NWSL historical game data fetcher backed by the American Soccer Analysis API.

The ASA API is free and unauthenticated.  Odds are unavailable — all odds
fields on the returned HistoricalGame objects are None.  The BacktestPipeline
treats such games as training-only; they build the Poisson strength model but
produce no value bets.

Usage::

    from bet.data.nwsl import NWSLDataFetcher

    fetcher = NWSLDataFetcher()
    games = fetcher.fetch()  # list[HistoricalGame]
"""

from __future__ import annotations

from .base import ASALeagueDataFetcher


class NWSLDataFetcher(ASALeagueDataFetcher):
    """Fetches NWSL game results from the American Soccer Analysis API."""

    league_slug = "nwsl"
    sport_slug = "nwsl"
