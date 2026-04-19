"""Tests for the MLSDataFetcher adapter."""

from __future__ import annotations

from datetime import UTC
from unittest.mock import MagicMock

from bet.backtesting.types import HistoricalGame
from bet.data.mls import MLSDataFetcher


def _mock_client(games: list[dict], teams: list[dict]) -> MagicMock:
    client = MagicMock()
    client.get_mls_games.return_value = games
    client.get_mls_teams.return_value = teams
    return client


_SAMPLE_TEAMS = [
    {"team_id": "ATL", "team_name": "Atlanta United FC"},
    {"team_id": "CHI", "team_name": "Chicago Fire FC"},
    {"team_id": "SEA", "team_name": "Seattle Sounders FC"},
]

_SAMPLE_GAMES = [
    {
        "game_id": "mls_2024_001",
        "date_time_utc": "2024-03-01 20:00:00",
        "home_score": 2,
        "away_score": 1,
        "home_team_id": "ATL",
        "away_team_id": "CHI",
        "season_name": "2024",
    },
    {
        "game_id": "mls_2024_002",
        "date_time_utc": "2024-03-08 22:30:00",
        "home_score": 0,
        "away_score": 3,
        "home_team_id": "CHI",
        "away_team_id": "SEA",
        "season_name": "2024",
    },
]


class TestMLSDataFetcherFetch:
    def test_fetch_returns_list(self) -> None:
        # Arrange
        fetcher = MLSDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert isinstance(result, list)

    def test_fetch_returns_historical_game_instances(self) -> None:
        # Arrange
        fetcher = MLSDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(isinstance(g, HistoricalGame) for g in result)

    def test_fetch_returns_correct_count(self) -> None:
        # Arrange
        fetcher = MLSDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert len(result) == 2

    def test_games_have_mls_sport_slug(self) -> None:
        # Arrange
        fetcher = MLSDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(g.sport == "mls" for g in result)

    def test_team_ids_resolved_to_names(self) -> None:
        # Arrange
        fetcher = MLSDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_team == "Atlanta United FC"
        assert result[0].away_team == "Chicago Fire FC"

    def test_scores_are_correct(self) -> None:
        # Arrange
        fetcher = MLSDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_score == 2
        assert result[0].away_score == 1

    def test_odds_are_none(self) -> None:
        # Arrange — ASA has no odds; all odds fields must be None
        fetcher = MLSDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        for game in result:
            assert game.home_win_odds is None
            assert game.away_win_odds is None
            assert game.closing_home_win_odds is None
            assert game.closing_away_win_odds is None

    def test_event_id_matches_game_id(self) -> None:
        # Arrange
        fetcher = MLSDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].event_id == "mls_2024_001"

    def test_game_date_is_utc_datetime(self) -> None:
        # Arrange
        fetcher = MLSDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].game_date.tzinfo == UTC

    def test_results_sorted_by_game_date(self) -> None:
        # Arrange — provide games in reverse order to verify sorting
        reversed_games = list(reversed(_SAMPLE_GAMES))
        fetcher = MLSDataFetcher(client=_mock_client(reversed_games, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].event_id == "mls_2024_001"
        assert result[1].event_id == "mls_2024_002"

    def test_unknown_team_id_falls_back_to_id(self) -> None:
        # Arrange
        games = [
            {
                "game_id": "mls_2024_999",
                "date_time_utc": "2024-04-01 20:00:00",
                "home_score": 1,
                "away_score": 1,
                "home_team_id": "UNKNOWN",
                "away_team_id": "ATL",
                "season_name": "2024",
            }
        ]
        fetcher = MLSDataFetcher(client=_mock_client(games, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_team == "UNKNOWN"

    def test_empty_games_returns_empty_list(self) -> None:
        # Arrange
        fetcher = MLSDataFetcher(client=_mock_client([], _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result == []


class TestMLSDataFetcherSeasons:
    def test_fetch_with_seasons_calls_get_games_once_per_season(self) -> None:
        # Arrange — two seasons should produce two API calls
        client = _mock_client([], _SAMPLE_TEAMS)
        fetcher = MLSDataFetcher(client=client, seasons=["2023", "2024"])

        # Act
        fetcher.fetch()

        # Assert
        assert client.get_mls_games.call_count == 2
        client.get_mls_games.assert_any_call(season_name="2023")
        client.get_mls_games.assert_any_call(season_name="2024")

    def test_fetch_without_seasons_calls_get_games_once(self) -> None:
        # Arrange — no seasons: single call without season filter
        client = _mock_client([], _SAMPLE_TEAMS)
        fetcher = MLSDataFetcher(client=client)

        # Act
        fetcher.fetch()

        # Assert
        client.get_mls_games.assert_called_once_with()

    def test_fetch_across_seasons_deduplicates_on_game_id(self) -> None:
        # Arrange — same game_id returned by two season queries must appear once
        game = _SAMPLE_GAMES[0]
        client = MagicMock()
        client.get_mls_teams.return_value = _SAMPLE_TEAMS
        client.get_mls_games.return_value = [game]  # same result for both seasons
        fetcher = MLSDataFetcher(client=client, seasons=["2024", "2024"])

        # Act
        result = fetcher.fetch()

        # Assert
        assert len(result) == 1

    def test_fetch_across_seasons_combines_results(self) -> None:
        # Arrange — each season returns one distinct game
        client = MagicMock()
        client.get_mls_teams.return_value = _SAMPLE_TEAMS
        client.get_mls_games.side_effect = [
            [_SAMPLE_GAMES[0]],
            [_SAMPLE_GAMES[1]],
        ]
        fetcher = MLSDataFetcher(client=client, seasons=["2023", "2024"])

        # Act
        result = fetcher.fetch()

        # Assert
        assert len(result) == 2
