"""Tests for the historical CSV data loader."""

from __future__ import annotations

import textwrap
from pathlib import Path

from bet.backtesting.loader import CSVDataLoader
from bet.backtesting.types import HistoricalGame

_NFL_CSV = textwrap.dedent("""\
    event_id,sport,home_team,away_team,game_date,home_score,away_score,\
home_win_odds,away_win_odds,draw_odds,closing_home_win_odds,\
closing_away_win_odds,closing_draw_odds
    nfl-1,nfl,Patriots,Chiefs,2023-09-10T20:00:00+00:00,27,20,\
1.90,1.90,,1.85,1.95,
    nfl-2,nfl,Cowboys,Eagles,2023-09-17T16:25:00+00:00,14,21,\
1.85,1.95,,1.80,2.00,
""")

_SOCCER_CSV = textwrap.dedent("""\
    event_id,sport,home_team,away_team,game_date,home_score,away_score,\
home_win_odds,away_win_odds,draw_odds,closing_home_win_odds,\
closing_away_win_odds,closing_draw_odds
    soc-1,soccer,Arsenal,Chelsea,2023-08-12T15:00:00+00:00,2,1,\
2.10,3.20,3.40,2.05,3.30,3.50
""")


class TestCSVDataLoader:
    def test_load_returns_historical_game_instances(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "games.csv"
        csv_file.write_text(_NFL_CSV)
        games = CSVDataLoader().load(str(csv_file))
        assert all(isinstance(g, HistoricalGame) for g in games)

    def test_load_nfl_returns_correct_count(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "games.csv"
        csv_file.write_text(_NFL_CSV)
        games = CSVDataLoader().load(str(csv_file))
        assert len(games) == 2

    def test_nfl_draw_odds_is_none(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "games.csv"
        csv_file.write_text(_NFL_CSV)
        games = CSVDataLoader().load(str(csv_file))
        assert games[0].draw_odds is None
        assert games[0].closing_draw_odds is None

    def test_soccer_draw_odds_parsed(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "games.csv"
        csv_file.write_text(_SOCCER_CSV)
        games = CSVDataLoader().load(str(csv_file))
        assert games[0].draw_odds is not None
        assert abs(games[0].draw_odds - 3.40) < 1e-9

    def test_game_fields_parsed_correctly(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "games.csv"
        csv_file.write_text(_NFL_CSV)
        g = CSVDataLoader().load(str(csv_file))[0]
        assert g.event_id == "nfl-1"
        assert g.home_team == "Patriots"
        assert g.away_team == "Chiefs"
        assert g.home_score == 27
        assert g.away_score == 20
        assert abs(g.home_win_odds - 1.90) < 1e-9

    def test_empty_csv_returns_empty_list(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "games.csv"
        csv_file.write_text(
            "event_id,sport,home_team,away_team,game_date,home_score,away_score,"
            "home_win_odds,away_win_odds,draw_odds,"
            "closing_home_win_odds,closing_away_win_odds,closing_draw_odds\n"
        )
        assert CSVDataLoader().load(str(csv_file)) == []
