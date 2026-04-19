"""Shared helpers for Elo-based feature extractors."""

from __future__ import annotations

from datetime import datetime

from ..modeling.types import TrainingExample

_SECONDS_PER_DAY = 86_400.0
_FORM_WINDOW = 5


class BaseEloExtractor:
    """Mixin providing rest-days and recent-form computations for Elo extractors.

    Subclasses must:
    - Set ``_default_rest_days`` as a class attribute (float).
    - Populate ``self._examples`` (list[TrainingExample]) before calling
      ``_days_since_last_game`` or ``_recent_form``.
    """

    _default_rest_days: float  # subclasses must set this as a class attribute
    _examples: list[TrainingExample]  # subclasses must populate this

    def _days_since_last_game(self, team: str, as_of: datetime) -> float:
        """Return days elapsed since the team's most recent completed game.

        Args:
            team: Team identifier.
            as_of: Reference timestamp; only games before this count.

        Returns:
            Days since last game, or ``_default_rest_days`` if no prior game.
        """
        prior = [
            ex
            for ex in self._examples
            if ex.outcome.final_at < as_of
            and team in (ex.feature_set.home_team, ex.feature_set.away_team)
        ]
        if not prior:
            return self._default_rest_days
        last = max(prior, key=lambda e: e.outcome.final_at)
        return (as_of - last.outcome.final_at).total_seconds() / _SECONDS_PER_DAY

    def _recent_form(self, team: str, as_of: datetime) -> float:
        """Return the team's win rate over the last ``_FORM_WINDOW`` games.

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
            if (ex.feature_set.home_team == team and ex.outcome.home_score > ex.outcome.away_score)
            or (ex.feature_set.away_team == team and ex.outcome.away_score > ex.outcome.home_score)
        )
        return wins / len(prior)
