"""NHL feature extractor — computes Elo-based features for game prediction.

For each game, the extractor rebuilds Elo ratings from scratch using only
games whose ``final_at`` timestamp is strictly before ``as_of``. This
guarantees no lookahead bias regardless of the order examples are provided.

NHL teams play an 82-game season on a schedule similar to the NBA. Back-to-back
games are meaningful predictors of fatigue. The default rest days prior is 2.0.

Note on draws: NHL regulation ties go to overtime and then a shootout, so every
game produces a winner. Outcomes are treated as binary (home win / away win)
regardless of whether the win came in regulation, OT, or shootout. Models that
need to distinguish regulation from OT wins should extend this extractor.
"""

from __future__ import annotations

from datetime import datetime

from ..modeling.elo import EloModel
from ..modeling.types import FeatureSet, TrainingExample
from ._base import BaseEloExtractor


class NHLFeatureExtractor(BaseEloExtractor):
    """Computes Elo-based features for NHL games.

    Rebuilds Elo ratings on every ``extract`` call using only historical
    games that completed before ``as_of``. Also computes rest-days and
    recent-form features from the same training window.

    Args:
        k_factor: K-factor passed to the internal ``EloModel``.
        home_advantage: Home advantage in Elo points. NHL home advantage is
            meaningful but smaller than NFL; 55 is a reasonable estimate.
        initial_rating: Starting rating for teams with no history.
        use_mov: If True, scale K by log goal differential. Goal differential
            is a strong predictor of future performance in hockey.
        mov_reference: Reference goal differential that yields K multiplier 1.0.
    """

    _default_rest_days: float = 2.0

    def __init__(
        self,
        k_factor: float = 20.0,
        home_advantage: float = 55.0,
        initial_rating: float = 1500.0,
        use_mov: bool = True,
        mov_reference: float = 2.0,
    ) -> None:
        self._k_factor = k_factor
        self._home_advantage = home_advantage
        self._initial_rating = initial_rating
        self._use_mov = use_mov
        self._mov_reference = mov_reference
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
        """Compute Elo, rest-days, and recent-form features for both teams.

        All features are computed using only games that completed strictly
        before ``as_of`` to prevent lookahead bias.

        Args:
            event_id: Identifier for the game being predicted.
            home_team: Home team identifier.
            away_team: Away team identifier.
            as_of: Cutoff timestamp; games at or after this time are excluded.

        Returns:
            FeatureSet with ``home_elo``, ``away_elo``, ``elo_diff``,
            ``home_rest_days``, ``away_rest_days``, ``home_form_5``, and
            ``away_form_5``.
        """
        model = EloModel(
            k_factor=self._k_factor,
            home_advantage=self._home_advantage,
            initial_rating=self._initial_rating,
            use_mov=self._use_mov,
            mov_reference=self._mov_reference,
        )
        for ex in self._examples:
            if ex.outcome.final_at < as_of:
                model.update(
                    ex.feature_set.home_team,
                    ex.feature_set.away_team,
                    ex.outcome.home_score,
                    ex.outcome.away_score,
                )

        home_elo = model.rating(home_team)
        away_elo = model.rating(away_team)

        return FeatureSet(
            event_id=event_id,
            sport="nhl",
            home_team=home_team,
            away_team=away_team,
            as_of=as_of,
            features={
                "home_elo": home_elo,
                "away_elo": away_elo,
                "elo_diff": home_elo - away_elo,
                "home_rest_days": self._days_since_last_game(home_team, as_of),
                "away_rest_days": self._days_since_last_game(away_team, as_of),
                "home_form_5": self._recent_form(home_team, as_of),
                "away_form_5": self._recent_form(away_team, as_of),
            },
        )
