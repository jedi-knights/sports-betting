"""Tests for the NWSLDataFetcher adapter."""

from __future__ import annotations

from unittest.mock import MagicMock

from bet.backtesting.types import HistoricalGame
from bet.data.nwsl import NWSLDataFetcher


def _mock_client(games: list[dict], teams: list[dict]) -> MagicMock:
    client = MagicMock()
    client.get_league_games.return_value = games
    client.get_league_teams.return_value = teams
    return client


_SAMPLE_TEAMS = [
    {"team_id": "NC", "team_name": "NC Courage"},
    {"team_id": "POR", "team_name": "Portland Thorns"},
    {"team_id": "CHI", "team_name": "Chicago Red Stars"},
]

_SAMPLE_GAMES = [
    {
        "game_id": "nwsl_2024_001",
        "date_time_utc": "2024-03-23 19:00:00",
        "home_score": 2,
        "away_score": 1,
        "home_team_id": "NC",
        "away_team_id": "POR",
        "season_name": "2024",
    },
    {
        "game_id": "nwsl_2024_002",
        "date_time_utc": "2024-03-30 18:00:00",
        "home_score": 0,
        "away_score": 0,
        "home_team_id": "POR",
        "away_team_id": "CHI",
        "season_name": "2024",
    },
]


class TestNWSLDataFetcherFetch:
    def test_fetch_returns_list(self) -> None:
        # Arrange
        fetcher = NWSLDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert isinstance(result, list)

    def test_fetch_returns_historical_game_instances(self) -> None:
        # Arrange
        fetcher = NWSLDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(isinstance(g, HistoricalGame) for g in result)

    def test_fetch_returns_correct_count(self) -> None:
        # Arrange
        fetcher = NWSLDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert len(result) == 2

    def test_games_have_nwsl_sport_slug(self) -> None:
        # Arrange
        fetcher = NWSLDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(g.sport == "nwsl" for g in result)

    def test_team_ids_resolved_to_names(self) -> None:
        # Arrange
        fetcher = NWSLDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert — team IDs must be replaced by human-readable names
        assert result[0].home_team == "NC Courage"
        assert result[0].away_team == "Portland Thorns"

    def test_scores_are_correct(self) -> None:
        # Arrange
        fetcher = NWSLDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_score == 2
        assert result[0].away_score == 1

    def test_odds_are_none(self) -> None:
        # Arrange — ASA API has no odds data; all odds fields must be None
        fetcher = NWSLDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        for game in result:
            assert game.home_win_odds is None
            assert game.away_win_odds is None
            assert game.closing_home_win_odds is None
            assert game.closing_away_win_odds is None

    def test_unknown_team_id_falls_back_to_id(self) -> None:
        # Arrange — game references a team_id not in the teams list
        games = [
            {
                "game_id": "nwsl_2024_999",
                "date_time_utc": "2024-04-06 19:00:00",
                "home_score": 1,
                "away_score": 0,
                "home_team_id": "UNKNOWN",
                "away_team_id": "NC",
                "season_name": "2024",
            }
        ]
        fetcher = NWSLDataFetcher(client=_mock_client(games, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert — unknown ID is used as-is rather than crashing
        assert result[0].home_team == "UNKNOWN"

    def test_empty_games_returns_empty_list(self) -> None:
        # Arrange
        fetcher = NWSLDataFetcher(client=_mock_client([], _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result == []

    def test_game_date_is_utc_datetime(self) -> None:
        # Arrange
        from datetime import UTC

        fetcher = NWSLDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert — game_date must be timezone-aware UTC
        assert result[0].game_date.tzinfo is not None
        assert result[0].game_date.tzinfo == UTC

    def test_event_id_matches_game_id(self) -> None:
        # Arrange
        fetcher = NWSLDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].event_id == "nwsl_2024_001"
