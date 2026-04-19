"""Tests for the American Soccer Analysis API client."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from bet.data.asa import ASAClient


class TestASAClientGames:
    def test_get_nwsl_games_returns_list(self) -> None:
        # Arrange
        payload = [
            {
                "game_id": "nwsl_2024_001",
                "date_time_utc": "2024-03-23 19:00:00",
                "home_score": 2,
                "away_score": 1,
                "home_team_id": "NC",
                "away_team_id": "POR",
                "season_name": "2024",
            }
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            client = ASAClient()

            # Act
            result = client.get_nwsl_games()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1

    def test_get_nwsl_games_returns_raw_dicts(self) -> None:
        # Arrange
        payload = [
            {
                "game_id": "nwsl_2024_001",
                "date_time_utc": "2024-03-23 19:00:00",
                "home_score": 2,
                "away_score": 1,
                "home_team_id": "NC",
                "away_team_id": "POR",
                "season_name": "2024",
            }
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            client = ASAClient()
            result = client.get_nwsl_games()

        # Assert
        assert result[0]["game_id"] == "nwsl_2024_001"
        assert result[0]["home_score"] == 2

    def test_get_nwsl_teams_returns_list(self) -> None:
        # Arrange
        payload = [
            {"team_id": "NC", "team_name": "NC Courage", "team_abbreviation": "NC"},
            {"team_id": "POR", "team_name": "Portland Thorns", "team_abbreviation": "POR"},
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            client = ASAClient()
            result = client.get_nwsl_teams()

        # Assert
        assert isinstance(result, list)
        assert result[0]["team_id"] == "NC"
        assert result[0]["team_name"] == "NC Courage"

    def test_empty_games_response_returns_empty_list(self) -> None:
        # Arrange
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"[]"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            client = ASAClient()
            result = client.get_nwsl_games()

        # Assert
        assert result == []


class TestASAClientMLS:
    def test_get_mls_games_returns_list(self) -> None:
        # Arrange
        payload = [
            {
                "game_id": "mls_2024_001",
                "date_time_utc": "2024-03-01 20:00:00",
                "home_score": 1,
                "away_score": 0,
                "home_team_id": "ATL",
                "away_team_id": "CHI",
                "season_name": "2024",
            }
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            client = ASAClient()

            # Act
            result = client.get_mls_games()

        # Assert
        assert isinstance(result, list)
        assert result[0]["game_id"] == "mls_2024_001"

    def test_get_mls_games_with_season_name_adds_query_params(self) -> None:
        # Arrange — verify the URL includes season_name and status filters
        captured_urls: list[str] = []

        def fake_urlopen(url):
            captured_urls.append(url)
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"[]"
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            client = ASAClient()

            # Act
            client.get_mls_games(season_name="2024")

        # Assert
        assert len(captured_urls) == 1
        assert "season_name=2024" in captured_urls[0]
        assert "status=FullTime" in captured_urls[0]

    def test_get_mls_games_without_season_omits_query_params(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(url):
            captured_urls.append(url)
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"[]"
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            client = ASAClient()

            # Act
            client.get_mls_games()

        # Assert
        assert "season_name" not in captured_urls[0]

    def test_get_mls_teams_returns_list(self) -> None:
        # Arrange
        payload = [
            {"team_id": "ATL", "team_name": "Atlanta United FC"},
            {"team_id": "CHI", "team_name": "Chicago Fire FC"},
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            client = ASAClient()
            result = client.get_mls_teams()

        # Assert
        assert result[0]["team_id"] == "ATL"
        assert result[0]["team_name"] == "Atlanta United FC"


class TestASAClientGeneric:
    """Tests for the generic league-agnostic client methods."""

    def _make_mock_resp(self, payload: list) -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_get_league_games_returns_list(self) -> None:
        # Arrange
        payload = [{"game_id": "usls_001", "date_time_utc": "2024-09-01 19:00:00"}]
        with patch("urllib.request.urlopen", return_value=self._make_mock_resp(payload)):
            client = ASAClient()

            # Act
            result = client.get_league_games("usls")

        # Assert
        assert isinstance(result, list)
        assert result[0]["game_id"] == "usls_001"

    def test_get_league_games_hits_correct_path(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(url):
            captured_urls.append(url)
            resp = MagicMock()
            resp.read.return_value = b"[]"
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ASAClient().get_league_games("usls")

        # Assert
        assert captured_urls[0].endswith("/usls/games")

    def test_get_league_games_with_season_adds_query_params(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(url):
            captured_urls.append(url)
            resp = MagicMock()
            resp.read.return_value = b"[]"
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ASAClient().get_league_games("mls", season_name="2024")

        # Assert
        assert "season_name=2024" in captured_urls[0]
        assert "status=FullTime" in captured_urls[0]

    def test_get_league_games_without_season_omits_query_params(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(url):
            captured_urls.append(url)
            resp = MagicMock()
            resp.read.return_value = b"[]"
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ASAClient().get_league_games("mls")

        # Assert
        assert "?" not in captured_urls[0]

    def test_get_league_teams_returns_list(self) -> None:
        # Arrange
        payload = [{"team_id": "NC", "team_name": "NC Courage"}]
        with patch("urllib.request.urlopen", return_value=self._make_mock_resp(payload)):
            client = ASAClient()

            # Act
            result = client.get_league_teams("nwsl")

        # Assert
        assert result[0]["team_name"] == "NC Courage"

    def test_get_league_teams_hits_correct_path(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(url):
            captured_urls.append(url)
            resp = MagicMock()
            resp.read.return_value = b"[]"
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ASAClient().get_league_teams("usls")

        # Assert
        assert captured_urls[0].endswith("/usls/teams")

    def test_nwsl_games_wrapper_delegates_to_get_league_games(self) -> None:
        # Arrange — backward-compat wrapper must produce same result as generic method
        payload = [{"game_id": "nwsl_001"}]
        with patch("urllib.request.urlopen", return_value=self._make_mock_resp(payload)):
            result = ASAClient().get_nwsl_games()
        assert result[0]["game_id"] == "nwsl_001"

    def test_mls_games_wrapper_delegates_to_get_league_games(self) -> None:
        # Arrange
        payload = [{"game_id": "mls_001"}]
        with patch("urllib.request.urlopen", return_value=self._make_mock_resp(payload)):
            result = ASAClient().get_mls_games()
        assert result[0]["game_id"] == "mls_001"
