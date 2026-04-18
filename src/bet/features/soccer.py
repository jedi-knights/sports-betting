"""Soccer feature extractor — computes attack/defense strength features.

Strength is estimated as the ratio of a team's average goals scored (or
conceded) to the league average, using only games completed before ``as_of``.
Values above 1.0 indicate above-average attack or defense weakness; values
below 1.0 indicate below-average.

These features feed directly into ``PoissonModel.predict`` as λ components:

    λ_home = home_baseline × home_attack × away_defense
    λ_away = away_baseline × away_attack × home_defense
"""

from __future__ import annotations

from datetime import datetime

from ..modeling.types import FeatureSet, TrainingExample

_DEFAULT_STRENGTH = 1.0


class SoccerFeatureExtractor:
    """Computes normalized attack and defense strength features for soccer.

    Attack strength is goals scored per game divided by the league average.
    Defense weakness is goals conceded per game divided by the league average.
    Teams with no historical data default to 1.0 (exactly average).

    Goals are tracked separately for home and away games to avoid mixing
    the two contexts; all games are combined for the normalization denominator.
    """

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
            sport="soccer",
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
