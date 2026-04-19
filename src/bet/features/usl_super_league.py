"""USL Super League feature extractor."""

from __future__ import annotations

from .soccer import SoccerLeagueFeatureExtractor


class USLSuperLeagueFeatureExtractor(SoccerLeagueFeatureExtractor):
    """Attack/defense strength extractor for the USL Super League."""

    league = "usl_super_league"
