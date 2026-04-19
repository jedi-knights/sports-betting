"""Shared test fixtures for the bet test suite."""

from __future__ import annotations

# Common CSV header for historical game fixture files.
# Used in integration tests and CLI tests that construct synthetic CSV data.
CSV_HEADER = (
    "event_id,sport,home_team,away_team,game_date,"
    "home_score,away_score,home_win_odds,away_win_odds,draw_odds,"
    "closing_home_win_odds,closing_away_win_odds,closing_draw_odds"
)
