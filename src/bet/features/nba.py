"""NBA feature extractor — computes Elo-based features for game prediction.

For each game, the extractor rebuilds Elo ratings from scratch using only
games whose ``final_at`` timestamp is strictly before ``as_of``. This
guarantees no lookahead bias regardless of the order examples are provided.

NBA teams play a dense 82-game schedule (roughly every 2–3 days). Rest
advantage is one of the most significant predictors in the NBA: back-to-back
games and travel fatigue measurably reduce win probability. The default rest
days prior (2.0) reflects this denser schedule relative to the NFL (7.0).
"""

from __future__ import annotations

from datetime import datetime

from ..modeling.elo import EloModel
from ..modeling.types import FeatureSet, TrainingExample
from ._base import BaseEloExtractor


class NBAFeatureExtractor(BaseEloExtractor):
    """Computes Elo-based features for NBA games.

    Rebuilds Elo ratings on every ``extract`` call using only historical
    games that completed before ``as_of``. Also computes rest-days and
    recent-form features from the same training window.

    NBA is an indoor sport — no weather features are included. Back-to-back
    game detection is captured implicitly through ``rest_days``.

    Args:
        k_factor: K-factor passed to the internal ``EloModel``.
        home_advantage: Home advantage (in Elo points) applied during
            prediction. NBA home advantage is smaller than NFL (~65 Elo
            points); 50 is a reasonable starting estimate.
        initial_rating: Starting rating for teams with no history.
        use_mov: If True, scale K by log margin so blowouts carry more weight.
        mov_reference: Reference margin (in points) that yields K multiplier
            1.0. NBA games are higher scoring than NFL; 10 points is a
            reasonable reference margin for NBA.
    """

    _default_rest_days: float = 2.0

    def __init__(
        self,
        k_factor: float = 20.0,
        home_advantage: float = 50.0,
        initial_rating: float = 1500.0,
        use_mov: bool = True,
        mov_reference: float = 10.0,
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
            sport="nba",
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
