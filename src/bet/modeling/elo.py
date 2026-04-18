"""Elo rating model for binary-outcome sports (NFL, NBA, etc.).

The Elo system maintains a rating per team. After each game, ratings shift
by K × (actual − expected). The expected score uses the logistic function
over the rating difference. Home field advantage is added to the home team's
effective rating before computing expected scores.
"""

from __future__ import annotations

import math

from .types import FeatureSet, ProbabilityEstimate, TrainingExample


class EloModel:
    """Elo rating model for binary-outcome sports.

    ``predict`` expects features produced by ``NFLFeatureExtractor``
    (or any extractor that provides ``home_elo`` and ``away_elo``).

    Args:
        k_factor: Magnitude of rating change per game. Higher values cause
            ratings to react faster but produce more noise.
        home_advantage: Points added to the home team's effective rating
            when computing expected scores. 65 is a standard NFL estimate.
        initial_rating: Starting rating for teams with no history.
    """

    model_id = "elo"

    def __init__(
        self,
        k_factor: float = 20.0,
        home_advantage: float = 65.0,
        initial_rating: float = 1500.0,
        use_mov: bool = True,
        mov_reference: float = 7.0,
    ) -> None:
        self._k_factor = k_factor
        self._home_advantage = home_advantage
        self._initial_rating = initial_rating
        self._use_mov = use_mov
        self._mov_reference = mov_reference
        self._ratings: dict[str, float] = {}

    def rating(self, team: str) -> float:
        """Return the current base Elo rating for a team.

        Args:
            team: Team identifier.

        Returns:
            The team's current rating, or ``initial_rating`` if unseen.
        """
        return self._ratings.get(team, self._initial_rating)

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Expected score for team A when facing team B under the Elo formula.

        Args:
            rating_a: Effective rating of team A (may include home advantage).
            rating_b: Effective rating of team B.

        Returns:
            Probability in (0, 1) that team A wins.
        """
        return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

    def _mov_multiplier(self, home_score: int, away_score: int) -> float:
        """Scale K by log margin so blowouts carry more information than squeakers.

        Normalised so that a one-TD (``mov_reference``-point) margin gives
        multiplier = 1.0. A 1-point win gives ~0.33; a 28-point blowout ~1.62.
        A draw always returns 1.0 because the margin is 0.
        """
        if not self._use_mov:
            return 1.0
        margin = abs(home_score - away_score)
        if margin == 0:
            return 1.0
        return math.log(margin + 1) / math.log(self._mov_reference + 1)

    def update(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
    ) -> None:
        """Update ratings given one game result.

        Home advantage is applied only when computing expected scores, not
        stored in the ratings. Stored ratings are always base values.

        Args:
            home_team: Home team identifier.
            away_team: Away team identifier.
            home_score: Goals / points scored by the home team.
            away_score: Goals / points scored by the away team.
        """
        effective_home = self.rating(home_team) + self._home_advantage
        effective_away = self.rating(away_team)

        expected_home = self.expected_score(effective_home, effective_away)

        if home_score > away_score:
            actual_home = 1.0
        elif home_score == away_score:
            actual_home = 0.5
        else:
            actual_home = 0.0

        k_eff = self._k_factor * self._mov_multiplier(home_score, away_score)

        self._ratings[home_team] = self.rating(home_team) + k_eff * (actual_home - expected_home)
        self._ratings[away_team] = self.rating(away_team) + k_eff * (
            (1.0 - actual_home) - (1.0 - expected_home)
        )

    def fit(self, examples: list[TrainingExample]) -> None:
        """Process historical examples in chronological order to build ratings.

        Args:
            examples: Labelled games; sorted by ``outcome.final_at`` before processing.
        """
        for ex in sorted(examples, key=lambda e: e.outcome.final_at):
            self.update(
                ex.feature_set.home_team,
                ex.feature_set.away_team,
                ex.outcome.home_score,
                ex.outcome.away_score,
            )

    def predict(self, features: FeatureSet) -> ProbabilityEstimate:
        """Predict win probabilities using Elo ratings from the feature set.

        Expects ``features.features["home_elo"]`` and ``features.features["away_elo"]``
        as base (pre-advantage) ratings. Home advantage is applied here.

        Args:
            features: Feature set produced by ``NFLFeatureExtractor``.

        Returns:
            A ProbabilityEstimate with ``draw=None`` (no draws in Elo sports).
        """
        home_elo = features.features["home_elo"]
        away_elo = features.features["away_elo"]
        effective_home = home_elo + self._home_advantage
        home_prob = self.expected_score(effective_home, away_elo)

        return ProbabilityEstimate(
            event_id=features.event_id,
            model_id=self.model_id,
            generated_at=features.as_of,
            home_win=home_prob,
            away_win=1.0 - home_prob,
            draw=None,
        )
