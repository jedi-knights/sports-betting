"""USL W League feature extractor."""

from __future__ import annotations

from .soccer import SoccerLeagueFeatureExtractor


class USLWLeagueFeatureExtractor(SoccerLeagueFeatureExtractor):
    """Attack/defense strength extractor for the USL W League."""

    league = "usl_w_league"
