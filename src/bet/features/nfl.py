"""NFL feature extractor — computes Elo-based features for game prediction.

For each game, the extractor rebuilds Elo ratings from scratch using only
games whose ``final_at`` timestamp is strictly before ``as_of``. This
guarantees no lookahead bias regardless of the order examples are provided.
"""

from __future__ import annotations

from datetime import datetime

from ..modeling.elo import EloModel
from ..modeling.types import FeatureSet, TrainingExample

_SECONDS_PER_DAY = 86_400.0
_DEFAULT_REST_DAYS = 7.0  # NFL teams play weekly; use as prior when no history
_FORM_WINDOW = 5


class NFLFeatureExtractor:
    """Computes Elo-based features for NFL games.

    Rebuilds Elo ratings on every ``extract`` call using only historical
    games that completed before ``as_of``. Also computes rest-days and
    recent-form features from the same training window.

    The computational cost is O(n) per extract where n is the number of
    historical games; acceptable for backtesting.

    Args:
        k_factor: K-factor passed to the internal ``EloModel``.
        home_advantage: Home advantage (in Elo points) passed to the internal
            ``EloModel`` and applied during prediction.
        initial_rating: Starting rating for teams with no history.
        use_mov: If True, scale K by log margin so blowouts carry more weight.
        mov_reference: Reference margin (in points) that yields K multiplier 1.0.
    """

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
        *,
        temperature: float | None = None,
        wind_mph: float | None = None,
        precipitation: bool = False,
    ) -> FeatureSet:
        """Compute Elo, rest-days, recent-form, and weather features for both teams.

        All features are computed using only games that completed strictly
        before ``as_of`` to prevent lookahead bias.

        Args:
            event_id: Identifier for the game being predicted.
            home_team: Home team identifier.
            away_team: Away team identifier.
            as_of: Cutoff timestamp; games at or after this time are excluded.
            temperature: Air temperature in Fahrenheit at game time. When
                ``None``, defaults to 60 °F — a neutral indoor-equivalent
                baseline. NFL weather impact becomes meaningful below ~40 °F.
            wind_mph: Wind speed in mph at game time. When ``None``, defaults
                to 0 mph. Wind above ~15 mph suppresses passing efficiency and
                scoring in open-air stadiums.
            precipitation: Whether rain or snow was present. Defaults to
                ``False``. Stored as ``is_precipitation`` (1.0/0.0) in the
                feature set so it is numerically compatible with all models.

        Returns:
            FeatureSet with ``home_elo``, ``away_elo``, ``elo_diff``,
            ``home_rest_days``, ``away_rest_days``, ``home_form_5``,
            ``away_form_5``, ``home_temperature``, ``wind_mph``, and
            ``is_precipitation``.
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
            sport="nfl",
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
                "home_temperature": temperature if temperature is not None else 60.0,
                "wind_mph": wind_mph if wind_mph is not None else 0.0,
                "is_precipitation": 1.0 if precipitation else 0.0,
            },
        )

    def _days_since_last_game(self, team: str, as_of: datetime) -> float:
        """Return days elapsed since the team's most recent completed game.

        Args:
            team: Team identifier.
            as_of: Reference timestamp; only games before this count.

        Returns:
            Days since last game, or ``_DEFAULT_REST_DAYS`` if no prior game.
        """
        prior = [
            ex
            for ex in self._examples
            if ex.outcome.final_at < as_of
            and team in (ex.feature_set.home_team, ex.feature_set.away_team)
        ]
        if not prior:
            return _DEFAULT_REST_DAYS
        last = max(prior, key=lambda e: e.outcome.final_at)
        return (as_of - last.outcome.final_at).total_seconds() / _SECONDS_PER_DAY

    def _recent_form(self, team: str, as_of: datetime) -> float:
        """Return the team's win rate over its last ``_FORM_WINDOW`` games.

        Args:
            team: Team identifier.
            as_of: Reference timestamp; only games before this count.

        Returns:
            Win rate in [0, 1], or 0.5 if the team has no prior games.
        """
        prior = sorted(
            (
                ex
                for ex in self._examples
                if ex.outcome.final_at < as_of
                and team in (ex.feature_set.home_team, ex.feature_set.away_team)
            ),
            key=lambda e: e.outcome.final_at,
        )[-_FORM_WINDOW:]
        if not prior:
            return 0.5
        wins = sum(
            1
            for ex in prior
            if (
                ex.feature_set.home_team == team
                and ex.outcome.home_score > ex.outcome.away_score
            )
            or (
                ex.feature_set.away_team == team
                and ex.outcome.away_score > ex.outcome.home_score
            )
        )
        return wins / len(prior)
