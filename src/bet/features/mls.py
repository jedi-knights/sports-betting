"""MLS (Major League Soccer) feature extractor."""

from __future__ import annotations

from .soccer import SoccerLeagueFeatureExtractor


class MLSFeatureExtractor(SoccerLeagueFeatureExtractor):
    """Attack/defense strength extractor for Major League Soccer."""

    league = "mls"
