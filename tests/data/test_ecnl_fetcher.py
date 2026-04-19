"""Tests for the ECNLDataFetcher adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from bet.backtesting.types import HistoricalGame
from bet.data.ecnl import ECNLDataFetcher

_COMPLETED_MATCH = {
    "matchID": 906430,
    "gameDate": "2025-09-06T10:00:00",
    "homeTeam": "NCFC Youth ECNL G13",
    "awayTeam": "Charlotte SA ECNL G13",
    "hometeamscore": 1,
    "awayteamscore": 3,
}

_SCHEDULED_MATCH = {
    "matchID": 906431,
    "gameDate": "2026-03-15T10:00:00",
    "homeTeam": "NCFC Youth ECNL G13",
    "awayTeam": "Triangle FC ECNL G13",
    "hometeamscore": None,
    "awayteamscore": None,
}

_SECOND_COMPLETED_MATCH = {
    "matchID": 906432,
    "gameDate": "2025-09-13T10:00:00",
    "homeTeam": "Charlotte SA ECNL G13",
    "awayTeam": "Pipeline SC ECNL G13",
    "hometeamscore": 2,
    "awayteamscore": 2,
}


def _mock_client(
    event_ids_by_season: dict[int, list[int]],
    flight_ids_by_event: dict[int, list[int]],
    schedules: list[dict],
) -> MagicMock:
    client = MagicMock()
    client.get_event_ids_for_season.side_effect = lambda sid: event_ids_by_season.get(sid, [])
    client.get_flight_ids_for_event.side_effect = lambda eid: flight_ids_by_event.get(eid, [])
    client.get_schedules_by_flight.return_value = schedules
    return client


class TestECNLDataFetcherFetch:
    def test_fetch_returns_list(self) -> None:
        # Arrange
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert isinstance(result, list)

    def test_fetch_returns_historical_game_instances(self) -> None:
        # Arrange
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(isinstance(g, HistoricalGame) for g in result)

    def test_games_have_ecnl_girls_sport_slug(self) -> None:
        # Arrange — season 69 is ECNL Girls
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(g.sport == "ecnl_girls" for g in result)

    def test_team_names_from_home_away_fields(self) -> None:
        # Arrange — AthleteOne embeds full team display names in homeTeam/awayTeam
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_team == "NCFC Youth ECNL G13"
        assert result[0].away_team == "Charlotte SA ECNL G13"

    def test_scores_are_correct(self) -> None:
        # Arrange
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].home_score == 1
        assert result[0].away_score == 3

    def test_only_completed_matches_included(self) -> None:
        # Arrange — null hometeamscore means not yet played; only non-null scores are results
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH, _SCHEDULED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert len(result) == 1
        assert result[0].event_id == "ecnl_906430"

    def test_scheduled_match_excluded(self) -> None:
        # Arrange
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_SCHEDULED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result == []

    def test_odds_are_none(self) -> None:
        # Arrange
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        for game in result:
            assert game.home_win_odds is None
            assert game.away_win_odds is None
            assert game.closing_home_win_odds is None
            assert game.closing_away_win_odds is None

    def test_event_id_prefixed_with_ecnl(self) -> None:
        # Arrange — prefix avoids collision with numeric IDs from other leagues
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].event_id == "ecnl_906430"

    def test_game_date_is_utc_datetime(self) -> None:
        # Arrange
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].game_date.tzinfo == UTC

    def test_game_date_parsed_correctly(self) -> None:
        # Arrange — gameDate "2025-09-06T10:00:00" → Sep 6 2025 10:00 UTC
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].game_date == datetime(2025, 9, 6, 10, 0, 0, tzinfo=UTC)

    def test_results_sorted_by_game_date(self) -> None:
        # Arrange — provide matches in reverse date order
        reversed_matches = [_SECOND_COMPLETED_MATCH, _COMPLETED_MATCH]
        client = _mock_client({69: [3925]}, {3925: [32626]}, reversed_matches)
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result[0].event_id == "ecnl_906430"
        assert result[1].event_id == "ecnl_906432"

    def test_empty_schedules_returns_empty_list(self) -> None:
        # Arrange
        client = _mock_client({69: [3925]}, {3925: [32626]}, [])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result == []

    def test_deduplicates_on_match_id(self) -> None:
        # Arrange — same match returned for two different flights (defensive dedup)
        client = _mock_client({69: [3925]}, {3925: [32626, 32624]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert len(result) == 1


class TestECNLDataFetcherCache:
    def test_event_ids_cached_across_fetch_calls(self) -> None:
        # Arrange — event ID lookup (HTML parse) should happen once per season, not per fetch()
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        fetcher.fetch()
        fetcher.fetch()

        # Assert
        assert client.get_event_ids_for_season.call_count == 1

    def test_flight_ids_cached_across_fetch_calls(self) -> None:
        # Arrange — flight ID lookup should happen once per event, not per fetch()
        client = _mock_client({69: [3925]}, {3925: [32626]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        fetcher.fetch()
        fetcher.fetch()

        # Assert
        assert client.get_flight_ids_for_event.call_count == 1


class TestECNLDataFetcherSportSlugs:
    def test_ecnl_boys_sport_slug(self) -> None:
        # Arrange — season 70 is ECNL Boys
        client = _mock_client({70: [3930]}, {3930: [32700]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[70])

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(g.sport == "ecnl_boys" for g in result)

    def test_ecrl_girls_sport_slug(self) -> None:
        # Arrange — season 71 is ECRL Girls
        client = _mock_client({71: [3940]}, {3940: [32800]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[71])

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(g.sport == "ecrl_girls" for g in result)

    def test_ecrl_boys_sport_slug(self) -> None:
        # Arrange — season 72 is ECRL Boys
        client = _mock_client({72: [3950]}, {3950: [32900]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[72])

        # Act
        result = fetcher.fetch()

        # Assert
        assert all(g.sport == "ecrl_boys" for g in result)


class TestECNLDataFetcherSeasons:
    def test_queries_all_season_ids(self) -> None:
        # Arrange
        client = _mock_client(
            {68: [3900], 69: [3925]},
            {3900: [32500], 3925: [32626]},
            [_COMPLETED_MATCH],
        )
        fetcher = ECNLDataFetcher(client=client, season_ids=[68, 69])

        # Act
        fetcher.fetch()

        # Assert
        assert client.get_event_ids_for_season.call_count == 2

    def test_no_events_for_season_returns_empty_list(self) -> None:
        # Arrange
        client = _mock_client({69: []}, {}, [])
        fetcher = ECNLDataFetcher(client=client, season_ids=[69])

        # Act
        result = fetcher.fetch()

        # Assert
        assert result == []

    def test_default_season_ids_cover_all_four_leagues(self) -> None:
        # Arrange — default should include Girls(69), Boys(70), RL Girls(71), RL Boys(72)
        from bet.data.ecnl import _DEFAULT_SEASON_IDS

        # Assert
        assert set(_DEFAULT_SEASON_IDS) == {69, 70, 71, 72}


class TestECNLSeasonConstants:
    def test_ecnl_girls_season_ids_exported(self) -> None:
        from bet.data.ecnl import ECNL_GIRLS_SEASON_IDS

        # Spot-check known seasons: 2015-16(5), 2022-23(41), 2025-26(69)
        assert 5 in ECNL_GIRLS_SEASON_IDS
        assert 41 in ECNL_GIRLS_SEASON_IDS
        assert 69 in ECNL_GIRLS_SEASON_IDS

    def test_ecnl_boys_season_ids_exported(self) -> None:
        from bet.data.ecnl import ECNL_BOYS_SEASON_IDS

        # Spot-check: 2017-18(10), 2022-23(42), 2025-26(70)
        assert 10 in ECNL_BOYS_SEASON_IDS
        assert 42 in ECNL_BOYS_SEASON_IDS
        assert 70 in ECNL_BOYS_SEASON_IDS

    def test_ecrl_girls_season_ids_exported(self) -> None:
        from bet.data.ecnl import ECRL_GIRLS_SEASON_IDS

        # Spot-check: 2021-22(35), 2023-24(51), 2025-26(71)
        assert 35 in ECRL_GIRLS_SEASON_IDS
        assert 51 in ECRL_GIRLS_SEASON_IDS
        assert 71 in ECRL_GIRLS_SEASON_IDS

    def test_ecrl_boys_season_ids_exported(self) -> None:
        from bet.data.ecnl import ECRL_BOYS_SEASON_IDS

        # Spot-check: 2021-22(36), 2023-24(52), 2025-26(72)
        assert 36 in ECRL_BOYS_SEASON_IDS
        assert 52 in ECRL_BOYS_SEASON_IDS
        assert 72 in ECRL_BOYS_SEASON_IDS

    def test_all_ecnl_season_ids_is_union_of_four_leagues(self) -> None:
        from bet.data.ecnl import (
            ALL_ECNL_SEASON_IDS,
            ECNL_BOYS_SEASON_IDS,
            ECNL_GIRLS_SEASON_IDS,
            ECRL_BOYS_SEASON_IDS,
            ECRL_GIRLS_SEASON_IDS,
        )

        expected = set(
            ECNL_GIRLS_SEASON_IDS
            + ECNL_BOYS_SEASON_IDS
            + ECRL_GIRLS_SEASON_IDS
            + ECRL_BOYS_SEASON_IDS
        )
        assert set(ALL_ECNL_SEASON_IDS) == expected

    def test_historical_girls_id_maps_to_ecnl_girls_slug(self) -> None:
        # Season 41 = ECNL Girls 2022-23
        client = _mock_client({41: [3000]}, {3000: [30000]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[41])

        result = fetcher.fetch()

        assert result[0].sport == "ecnl_girls"

    def test_historical_boys_id_maps_to_ecnl_boys_slug(self) -> None:
        # Season 42 = ECNL Boys 2022-23
        client = _mock_client({42: [3001]}, {3001: [30001]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[42])

        result = fetcher.fetch()

        assert result[0].sport == "ecnl_boys"

    def test_historical_ecrl_girls_id_maps_to_ecrl_girls_slug(self) -> None:
        # Season 43 = ECRL Girls 2022-23
        client = _mock_client({43: [3002]}, {3002: [30002]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[43])

        result = fetcher.fetch()

        assert result[0].sport == "ecrl_girls"

    def test_historical_ecrl_boys_id_maps_to_ecrl_boys_slug(self) -> None:
        # Season 44 = ECRL Boys 2022-23
        client = _mock_client({44: [3003]}, {3003: [30003]}, [_COMPLETED_MATCH])
        fetcher = ECNLDataFetcher(client=client, season_ids=[44])

        result = fetcher.fetch()

        assert result[0].sport == "ecrl_boys"
