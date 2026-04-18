"""Lookahead bias guard for the walk-forward pipeline."""

from __future__ import annotations

from datetime import datetime

from .types import HistoricalGame


class LookaheadBiasError(Exception):
    """Raised when a training dataset contains games from on or after as_of."""


def assert_no_lookahead(
    training_games: list[HistoricalGame],
    as_of: datetime,
) -> None:
    """Raise LookaheadBiasError if any training game is not strictly before as_of.

    Args:
        training_games: Games used to train the model at this pipeline step.
        as_of: The date of the test game being predicted.

    Raises:
        LookaheadBiasError: If any game in training_games has a game_date
            that is on or after as_of.
    """
    for game in training_games:
        if game.game_date >= as_of:
            raise LookaheadBiasError(
                f"lookahead bias: {game.event_id} at {game.game_date} "
                f"is not strictly before as_of={as_of}"
            )
