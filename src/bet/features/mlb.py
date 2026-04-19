"""MLB feature extractor — computes Elo-based features for game prediction.

For each game, the extractor rebuilds Elo ratings from scratch using only
games whose ``final_at`` timestamp is strictly before ``as_of``. This
guarantees no lookahead bias regardless of the order examples are provided.

MLB teams play a 162-game season, often in series of 3–4 consecutive games
against the same opponent. Rest is nearly a constant (teams play almost
every day), so ``rest_days`` captures meaningful variance only around
scheduled off-days. The default rest days prior is 1.0.

Note: Starting pitcher is the dominant predictor in MLB but requires per-game
pitcher data not available in the standard ``HistoricalGame`` schema. These
features therefore use team-level Elo and rolling form as a baseline. Adding
pitcher-adjusted Elo is a recommended next step when pitcher data is available.
"""

from __future__ import annotations

from datetime import datetime

from ..modeling.elo import EloModel
from ..modeling.types import FeatureSet, TrainingExample
from ._base import BaseEloExtractor


class MLBFeatureExtractor(BaseEloExtractor):
    """Computes Elo-based features for MLB games.

    Rebuilds Elo ratings on every ``extract`` call using only historical
    games that completed before ``as_of``. Also computes rest-days and
    recent-form features from the same training window.

    Args:
        k_factor: K-factor passed to the internal ``EloModel``. A lower
            value is appropriate for MLB (high variance sport); 12–15 is
            a common range.
        home_advantage: Home advantage in Elo points. MLB home advantage is
            modest; 35 is a reasonable estimate.
        initial_rating: Starting rating for teams with no history.
        use_mov: If True, scale K by log run differential. Run differential
            in baseball is a known predictor of future performance.
        mov_reference: Reference run differential that yields K multiplier 1.0.
    """

    _default_rest_days: float = 1.0

    def __init__(
        self,
        k_factor: float = 15.0,
        home_advantage: float = 35.0,
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
            sport="mlb",
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
