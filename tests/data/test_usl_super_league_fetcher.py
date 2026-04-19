"""Tests for the USLSuperLeagueDataFetcher adapter."""

from __future__ import annotations

from datetime import UTC
from unittest.mock import MagicMock

from bet.backtesting.types import HistoricalGame
from bet.data.usl_super_league import USLSuperLeagueDataFetcher


def _mock_client(games: list[dict], teams: list[dict]) -> MagicMock:
    client = MagicMock()
    client.get_league_games.return_value = games
    client.get_league_teams.return_value = teams
    return client


_SAMPLE_TEAMS = [
    {"team_id": "CHI", "team_name": "Chicago Red Stars"},
    {"team_id": "KC", "team_name": "Kansas City Current"},
    {"team_id": "SEA", "team_name": "Seattle Reign FC"},
]

_SAMPLE_GAMES = [
    {
        "game_id": "usls_2024_001",
        "date_time_utc": "2024-08-17 19:00:00",
        "home_score": 2,
        "away_score": 0,
        "home_team_id": "CHI",
        "away_team_id": "KC",
        "season_name": "2024-25",
    },
    {
        "game_id": "usls_2024_002",
        "date_time_utc": "2024-08-24 18:00:00",
        "home_score": 1,
        "away_score": 1,
        "home_team_id": "KC",
        "away_team_id": "SEA",
        "season_name": "2024-25",
    },
]


class TestUSLSuperLeagueDataFetcherFetch:
    def test_fetch_returns_list(self) -> None:
        # Arrange
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert isinstance(result, list)

    def test_fetch_returns_historical_game_instances(self) -> None:
        # Arrange
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(isinstance(g, HistoricalGame) for g in result)

    def test_fetch_returns_correct_count(self) -> None:
        # Arrange
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert len(result) == 2

    def test_games_have_usl_super_league_sport_slug(self) -> None:
        # Arrange — sport slug must match the CLI/extractor slug
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(g.sport == "usl_super_league" for g in result)

    def test_client_queried_with_usls_league_slug(self) -> None:
        # Arrange — the ASA API path for USL Super League is "usls"
        client = _mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS)
        fetcher = USLSuperLeagueDataFetcher(client=client)

        # Act
        fetcher.fetch()

        # Assert
        client.get_league_games.assert_called_once_with("usls")
        client.get_league_teams.assert_called_once_with("usls")

    def test_team_ids_resolved_to_names(self) -> None:
        # Arrange
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_team == "Chicago Red Stars"
        assert result[0].away_team == "Kansas City Current"

    def test_scores_are_correct(self) -> None:
        # Arrange
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_score == 2
        assert result[0].away_score == 0

    def test_odds_are_none(self) -> None:
        # Arrange
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

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
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].event_id == "usls_2024_001"

    def test_game_date_is_utc_datetime(self) -> None:
        # Arrange
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(_SAMPLE_GAMES, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].game_date.tzinfo == UTC

    def test_results_sorted_by_game_date(self) -> None:
        # Arrange — reversed input must still come out sorted
        reversed_games = list(reversed(_SAMPLE_GAMES))
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(reversed_games, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].event_id == "usls_2024_001"
        assert result[1].event_id == "usls_2024_002"

    def test_unknown_team_id_falls_back_to_id(self) -> None:
        # Arrange
        games = [
            {
                "game_id": "usls_2024_999",
                "date_time_utc": "2024-09-01 19:00:00",
                "home_score": 1,
                "away_score": 0,
                "home_team_id": "UNKNOWN",
                "away_team_id": "CHI",
                "season_name": "2024-25",
            }
        ]
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client(games, _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_team == "UNKNOWN"

    def test_empty_games_returns_empty_list(self) -> None:
        # Arrange
        fetcher = USLSuperLeagueDataFetcher(client=_mock_client([], _SAMPLE_TEAMS))

        # Act
        result = fetcher.fetch()

        # Assert
        assert result == []

    def test_fetch_with_seasons_queries_per_season(self) -> None:
        # Arrange
        client = _mock_client([], _SAMPLE_TEAMS)
        fetcher = USLSuperLeagueDataFetcher(client=client, seasons=["2024-25", "2025-26"])

        # Act
        fetcher.fetch()

        # Assert
        assert client.get_league_games.call_count == 2
        client.get_league_games.assert_any_call("usls", season_name="2024-25")
        client.get_league_games.assert_any_call("usls", season_name="2025-26")
