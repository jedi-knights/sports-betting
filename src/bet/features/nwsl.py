"""NWSL (National Women's Soccer League) feature extractor."""

from __future__ import annotations

from .soccer import SoccerLeagueFeatureExtractor


class NWSLFeatureExtractor(SoccerLeagueFeatureExtractor):
    """Attack/defense strength extractor for the National Women's Soccer League."""

    league = "nwsl"
