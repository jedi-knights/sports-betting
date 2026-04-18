"""Tests for the lookahead bias guard."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from bet.backtesting.guard import LookaheadBiasError, assert_no_lookahead
from bet.backtesting.types import HistoricalGame


def _game(event_id: str, days_offset: int) -> HistoricalGame:
    base = datetime(2023, 9, 7, tzinfo=UTC)
    d = base + timedelta(days=days_offset)
    return HistoricalGame(
        event_id=event_id,
        sport="nfl",
        home_team="A",
        away_team="B",
        game_date=d,
        home_score=21,
        away_score=17,
        home_win_odds=1.9,
        away_win_odds=1.9,
        draw_odds=None,
        closing_home_win_odds=1.85,
        closing_away_win_odds=1.95,
        closing_draw_odds=None,
    )


class TestAssertNoLookahead:
    def test_empty_list_passes(self) -> None:
        as_of = datetime(2023, 10, 1, tzinfo=UTC)
        assert_no_lookahead([], as_of)  # should not raise

    def test_all_before_as_of_passes(self) -> None:
        games = [_game("g1", 0), _game("g2", 7), _game("g3", 14)]
        as_of = datetime(2023, 10, 1, tzinfo=UTC)
        assert_no_lookahead(games, as_of)  # should not raise

    def test_raises_when_game_equals_as_of(self) -> None:
        as_of = datetime(2023, 9, 7, tzinfo=UTC)
        games = [_game("g1", 0)]  # game_date == as_of
        with pytest.raises(LookaheadBiasError):
            assert_no_lookahead(games, as_of)

    def test_raises_when_game_after_as_of(self) -> None:
        as_of = datetime(2023, 9, 7, tzinfo=UTC)
        games = [_game("g1", -7), _game("future", 7)]  # future is after as_of
        with pytest.raises(LookaheadBiasError, match="future"):
            assert_no_lookahead(games, as_of)

    def test_error_message_contains_event_id(self) -> None:
        as_of = datetime(2023, 9, 7, tzinfo=UTC)
        with pytest.raises(LookaheadBiasError, match="bad-game-99"):
            assert_no_lookahead([_game("bad-game-99", 1)], as_of)
