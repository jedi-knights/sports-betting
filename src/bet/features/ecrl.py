"""ECRL (Elite Clubs Regional League) feature extractor.

ECRL is a model-only league — no bookmaker odds market exists for it.
Data must be supplied via StaticOddsProvider (historical CSV files).
"""

from __future__ import annotations

from .soccer import SoccerLeagueFeatureExtractor


class ECRLFeatureExtractor(SoccerLeagueFeatureExtractor):
    """Attack/defense strength extractor for the Elite Clubs Regional League (youth)."""

    league = "ecrl"
