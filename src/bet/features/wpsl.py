"""WPSL (Women's Premier Soccer League) feature extractor.

WPSL is a model-only league — no bookmaker odds market exists for it.
Data must be supplied via StaticOddsProvider (historical CSV files).
"""

from __future__ import annotations

from .soccer import SoccerLeagueFeatureExtractor


class WPSLFeatureExtractor(SoccerLeagueFeatureExtractor):
    """Attack/defense strength extractor for the Women's Premier Soccer League."""

    league = "wpsl"
