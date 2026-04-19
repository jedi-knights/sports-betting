"""ECNL (Elite Clubs National League) feature extractor.

ECNL is a model-only league — no bookmaker odds market exists for it.
Data must be supplied via StaticOddsProvider (historical CSV files).
"""

from __future__ import annotations

from .soccer import SoccerLeagueFeatureExtractor


class ECNLFeatureExtractor(SoccerLeagueFeatureExtractor):
    """Attack/defense strength extractor for the Elite Clubs National League (youth)."""

    league = "ecnl"
