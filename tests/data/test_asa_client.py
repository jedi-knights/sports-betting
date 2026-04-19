"""Tests for the American Soccer Analysis API client."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

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
