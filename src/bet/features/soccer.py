"""Base feature extractor for all soccer leagues.

Each soccer league has its own extractor subclass that inherits this
algorithm unchanged but stamps the correct league slug into the FeatureSet.
The attack/defense strength model is described in the module docstring for
the individual league modules.

Attack strength = goals scored per game / league average.
Defense weakness = goals conceded per game / league average.
Values > 1.0 are above-average; values < 1.0 are below-average.
Teams with no history default to 1.0 (league-average).
"""

from __future__ import annotations

from datetime import datetime

from ..modeling.types import FeatureSet, TrainingExample

_DEFAULT_STRENGTH = 1.0


class SoccerLeagueFeatureExtractor:
    """Shared Poisson attack/defense extractor for all soccer leagues.

    Subclasses set ``league`` to the slug that appears in FeatureSet.sport.
    The extraction algorithm is identical across leagues; strength ratings
    built from one league's data must never be mixed with another's.
    """

    league: str = "soccer"

    def __init__(self) -> None:
        self._examples: list[TrainingExample] = []

    def fit(self, examples: list[TrainingExample]) -> None:
        """Store historical examples for use during feature extraction.

        Args:
            examples: All available historical games; filtered by timestamp
                at extract time to enforce the lookahead guard.
        """
        self._examples = sorted(examples, key=lambda e: e.outcome.final_at)

    def extract(
        self,
        event_id: str,
        home_team: str,
        away_team: str,
        as_of: datetime,
    ) -> FeatureSet:
        """Compute normalized attack/defense strengths for both teams.

        Only games whose ``final_at`` is strictly before ``as_of`` are used.
        Unknown teams (no history) receive strength 1.0.

        Args:
            event_id: Identifier for the game being predicted.
            home_team: Home team identifier.
            away_team: Away team identifier.
            as_of: Cutoff timestamp; no data at or after this is used.

        Returns:
            FeatureSet with ``home_attack``, ``home_defense``,
            ``away_attack``, and ``away_defense``.
        """
        past = [ex for ex in self._examples if ex.outcome.final_at < as_of]

        goals_scored: dict[str, list[int]] = {}
        goals_conceded: dict[str, list[int]] = {}
        all_goals: list[int] = []

        for ex in past:
            ht = ex.feature_set.home_team
            at = ex.feature_set.away_team
            hg = ex.outcome.home_score
            ag = ex.outcome.away_score

            goals_scored.setdefault(ht, []).append(hg)
            goals_scored.setdefault(at, []).append(ag)
            goals_conceded.setdefault(ht, []).append(ag)
            goals_conceded.setdefault(at, []).append(hg)
            all_goals.extend([hg, ag])

        league_avg = sum(all_goals) / len(all_goals) if all_goals else 1.0

        def _strength(team: str, stat: dict[str, list[int]]) -> float:
            games = stat.get(team, [])
            if not games or league_avg == 0.0:
                return _DEFAULT_STRENGTH
            return (sum(games) / len(games)) / league_avg

        return FeatureSet(
            event_id=event_id,
            sport=self.league,
            home_team=home_team,
            away_team=away_team,
            as_of=as_of,
            features={
                "home_attack": _strength(home_team, goals_scored),
                "home_defense": _strength(home_team, goals_conceded),
                "away_attack": _strength(away_team, goals_scored),
                "away_defense": _strength(away_team, goals_conceded),
            },
        )


# Keep the old name as an alias so any external code that imported
# SoccerFeatureExtractor continues to work until fully migrated.
SoccerFeatureExtractor = SoccerLeagueFeatureExtractor
