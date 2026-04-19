"""EPL (English Premier League) feature extractor."""

from __future__ import annotations

from .soccer import SoccerLeagueFeatureExtractor


class EPLFeatureExtractor(SoccerLeagueFeatureExtractor):
    """Attack/defense strength extractor for the English Premier League."""

    league = "epl"
