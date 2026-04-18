"""Domain types for the Backtesting context."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HistoricalGame:
    """A completed game with market odds and closing line data.

    Used by the walk-forward pipeline to both train models and evaluate
    value bets against actual outcomes.

    Attributes:
        event_id: Unique identifier for the game.
        sport: Sport code (``"nfl"``, ``"soccer"``).
        home_team: Home team name or identifier.
        away_team: Away team name or identifier.
        game_date: UTC datetime when the game was played.
        home_score: Final score for the home team.
        away_score: Final score for the away team.
        home_win_odds: Opening decimal odds for home win.
        away_win_odds: Opening decimal odds for away win.
        draw_odds: Opening decimal odds for draw. ``None`` for binary sports.
        closing_home_win_odds: Closing decimal odds for home win (for CLV).
        closing_away_win_odds: Closing decimal odds for away win (for CLV).
        closing_draw_odds: Closing decimal odds for draw. ``None`` for binary sports.
        temperature: Air temperature in Fahrenheit at game time. ``None`` when
            not available; the feature extractor defaults to 60 °F in that case.
        wind_mph: Wind speed in mph at game time. ``None`` when not available;
            the feature extractor defaults to 0 mph in that case.
        precipitation: Whether rain or snow was present at game time. Defaults
            to ``False`` when the data is absent.
    """

    event_id: str
    sport: str
    home_team: str
    away_team: str
    game_date: datetime
    home_score: int
    away_score: int
    home_win_odds: float
    away_win_odds: float
    draw_odds: float | None
    closing_home_win_odds: float
    closing_away_win_odds: float
    closing_draw_odds: float | None
    temperature: float | None = field(default=None)
    wind_mph: float | None = field(default=None)
    precipitation: bool = field(default=False)
