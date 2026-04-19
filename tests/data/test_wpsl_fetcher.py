"""Tests for the WPSLDataFetcher adapter."""

from __future__ import annotations

from datetime import UTC
from unittest.mock import MagicMock

from bet.backtesting.types import HistoricalGame
from bet.data.wpsl import WPSLDataFetcher

_COMPETITIONS_2025 = [
    {"id": 79, "name": "WPSL 2025", "yearRefId": 7},
    {"id": 80, "name": "WPSL Division II 2025", "yearRefId": 7},
    {"id": 26, "name": "WPSL U21 2025", "yearRefId": 7},
]

_COMPETITIONS_2024 = [
    {"id": 18, "name": "WPSL 2024", "yearRefId": 6},
    {"id": 19, "name": "WPSL U21 2024", "yearRefId": 6},
]

_ENDED_MATCH = {
    "id": 21914,
    "startTime": "2025-05-11T01:00:00.000Z",
    "matchStatus": "ENDED",
    "team1Score": 2,
    "team2Score": 1,
    "team1": {"id": 10877, "name": "City SC Utah"},
    "team2": {"id": 10878, "name": "Utah Surf"},
}

_POSTPONED_MATCH = {
    "id": 21999,
    "startTime": "2025-06-01T00:00:00.000Z",
    "matchStatus": "POSTPONED",
    "team1Score": 0,
    "team2Score": 0,
    "team1": {"id": 10877, "name": "City SC Utah"},
    "team2": {"id": 10879, "name": "Griffins FC"},
}

_SECOND_ENDED_MATCH = {
    "id": 21918,
    "startTime": "2025-05-14T00:00:00.000Z",
    "matchStatus": "ENDED",
    "team1Score": 0,
    "team2Score": 6,
    "team1": {"id": 10880, "name": "Griffins FC"},
    "team2": {"id": 10878, "name": "Utah Surf"},
}


def _mock_client(competitions_by_year: dict[int, list[dict]], matches: list[dict]) -> MagicMock:
    client = MagicMock()
    client.get_competitions.side_effect = lambda org_key, year_ref_id: competitions_by_year.get(
        year_ref_id, []
    )
    client.get_matches.return_value = matches
    return client


class TestWPSLDataFetcherFetch:
    def test_fetch_returns_list(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert isinstance(result, list)

    def test_fetch_returns_historical_game_instances(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(isinstance(g, HistoricalGame) for g in result)

    def test_games_have_wpsl_sport_slug(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(g.sport == "wpsl" for g in result)

    def test_team_names_from_embedded_objects(self) -> None:
        # Arrange — Squadi embeds team names directly in match; no separate lookup
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_team == "City SC Utah"
        assert result[0].away_team == "Utah Surf"

    def test_scores_are_correct(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_score == 2
        assert result[0].away_score == 1

    def test_only_ended_matches_included(self) -> None:
        # Arrange — mix of ENDED and POSTPONED; only ENDED should appear
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH, _POSTPONED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert len(result) == 1
        assert result[0].event_id == "wpsl_21914"

    def test_postponed_match_not_included(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [_POSTPONED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result == []

    def test_odds_are_none(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        for game in result:
            assert game.home_win_odds is None
            assert game.away_win_odds is None
            assert game.closing_home_win_odds is None
            assert game.closing_away_win_odds is None

    def test_event_id_prefixed_with_wpsl(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert — prefixed to avoid collision with other leagues' numeric IDs
        assert result[0].event_id == "wpsl_21914"

    def test_game_date_is_utc_datetime(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].game_date.tzinfo == UTC

    def test_game_date_parsed_correctly(self) -> None:
        # Arrange — startTime "2025-05-11T01:00:00.000Z" → May 11 2025 01:00 UTC
        from datetime import datetime

        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].game_date == datetime(2025, 5, 11, 1, 0, 0, tzinfo=UTC)

    def test_results_sorted_by_game_date(self) -> None:
        # Arrange — provide matches in reverse date order
        reversed_matches = [_SECOND_ENDED_MATCH, _ENDED_MATCH]
        client = _mock_client({7: _COMPETITIONS_2025}, reversed_matches)
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].event_id == "wpsl_21914"
        assert result[1].event_id == "wpsl_21918"

    def test_empty_matches_returns_empty_list(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result == []


class TestWPSLDataFetcherCompetitionFilter:
    def test_main_wpsl_competition_included(self) -> None:
        # Arrange
        client = _mock_client({7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        fetcher.fetch()

        # Assert — only comp id 79 (WPSL 2025) should be fetched, not 80 or 26
        client.get_matches.assert_called_once_with(competition_id=79)

    def test_u21_competition_excluded(self) -> None:
        # Arrange — only U21 competitions in the list
        comps = [{"id": 26, "name": "WPSL U21 2025", "yearRefId": 7}]
        client = _mock_client({7: comps}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert — no matches should be fetched for U21 comps
        client.get_matches.assert_not_called()
        assert result == []

    def test_division_ii_competition_excluded(self) -> None:
        # Arrange
        comps = [{"id": 80, "name": "WPSL Division II 2025", "yearRefId": 7}]
        client = _mock_client({7: comps}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert
        client.get_matches.assert_not_called()
        assert result == []


class TestWPSLDataFetcherYears:
    def test_queries_all_year_ref_ids(self) -> None:
        # Arrange — two years, each with one main competition
        client = _mock_client({6: _COMPETITIONS_2024, 7: _COMPETITIONS_2025}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[6, 7])

        # Act
        fetcher.fetch()

        # Assert — get_competitions called once per year
        assert client.get_competitions.call_count == 2

    def test_deduplicates_on_match_id(self) -> None:
        # Arrange — same match returned for two competitions (defensive dedup)
        comps = [
            {"id": 79, "name": "WPSL 2025", "yearRefId": 7},
            {"id": 81, "name": "WPSL 2025 Finals", "yearRefId": 7},
        ]
        client = _mock_client({7: comps}, [_ENDED_MATCH])
        fetcher = WPSLDataFetcher(client=client, year_ref_ids=[7])

        # Act
        result = fetcher.fetch()

        # Assert — duplicate game_id produces only one entry
        assert len(result) == 1
