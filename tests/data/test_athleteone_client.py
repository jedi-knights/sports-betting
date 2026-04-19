"""Tests for the AthleteOne API client."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from bet.data.athleteone import AthleteOneClient

_HTML_EVENT_LIST = (
    "<select>"
    '<option value="0">--- Select ---</option>'
    '<option value="3925" >ECNL Girls Mid-Atlantic 2025-26</option>'
    '<option value="3926" >ECNL Girls Midwest 2025-26</option>'
    "</select>"
)

_FLIGHT_IDS_PAYLOAD = {
    "result": "success",
    "data": {
        "girlsDivAndFlightList": [
            {
                "divisionID": 18535,
                "divisionName": "G2013",
                "flightList": [
                    {
                        "divisionID": 18535,
                        "flightID": 32626,
                        "flightName": "ECNL",
                        "teamsCount": 10,
                        "hasActiveSchedule": True,
                        "hideSettings": 0,
                    }
                ],
            },
            {
                "divisionID": 18536,
                "divisionName": "G2012",
                "flightList": [
                    {
                        "divisionID": 18536,
                        "flightID": 32624,
                        "flightName": "ECNL",
                        "teamsCount": 10,
                        "hasActiveSchedule": True,
                        "hideSettings": 0,
                    }
                ],
            },
        ],
        "boysDivAndFlightList": [],
    },
}

_SCHEDULES_PAYLOAD = {
    "result": "success",
    "data": [
        {
            "matchID": 906430,
            "gameDate": "2025-09-06T10:00:00",
            "homeTeam": "NCFC Youth ECNL G13",
            "awayTeam": "Charlotte SA ECNL G13",
            "hometeamscore": 1,
            "awayteamscore": 3,
        },
        {
            "matchID": 906431,
            "gameDate": "2025-09-13T10:00:00",
            "homeTeam": "Charlotte SA ECNL G13",
            "awayTeam": "Pipeline SC ECNL G13",
            "hometeamscore": None,
            "awayteamscore": None,
        },
    ],
}


def _mock_resp(content: bytes) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.read.return_value = content
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestAthleteOneClientEventIds:
    def test_get_event_ids_returns_list(self) -> None:
        # Arrange
        with patch("urllib.request.urlopen", return_value=_mock_resp(_HTML_EVENT_LIST.encode())):
            # Act
            result = AthleteOneClient().get_event_ids_for_season(69)

        # Assert
        assert isinstance(result, list)

    def test_get_event_ids_returns_correct_ids(self) -> None:
        # Arrange
        with patch("urllib.request.urlopen", return_value=_mock_resp(_HTML_EVENT_LIST.encode())):
            # Act
            result = AthleteOneClient().get_event_ids_for_season(69)

        # Assert
        assert result == [3925, 3926]

    def test_get_event_ids_excludes_zero_placeholder(self) -> None:
        # Arrange — the "--- Select ---" option has value="0" and must be excluded
        with patch("urllib.request.urlopen", return_value=_mock_resp(_HTML_EVENT_LIST.encode())):
            # Act
            result = AthleteOneClient().get_event_ids_for_season(69)

        # Assert
        assert 0 not in result

    def test_get_event_ids_empty_select_returns_empty_list(self) -> None:
        # Arrange
        html = '<select><option value="0">--- Select ---</option></select>'
        with patch("urllib.request.urlopen", return_value=_mock_resp(html.encode())):
            # Act
            result = AthleteOneClient().get_event_ids_for_season(69)

        # Assert
        assert result == []

    def test_get_event_ids_sends_origin_header(self) -> None:
        # Arrange — Squadi-style CORS check; Origin must be theecnl.com
        captured_headers: list[dict] = []

        def fake_urlopen(req):
            captured_headers.append(dict(req.headers))
            return _mock_resp(b"<select></select>")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            AthleteOneClient().get_event_ids_for_season(69)

        # Assert
        assert "Origin" in captured_headers[0]

    def test_get_event_ids_sends_user_agent_header(self) -> None:
        # Arrange
        captured_headers: list[dict] = []

        def fake_urlopen(req):
            captured_headers.append(dict(req.headers))
            return _mock_resp(b"<select></select>")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            AthleteOneClient().get_event_ids_for_season(69)

        # Assert
        assert "User-agent" in captured_headers[0]

    def test_get_event_ids_includes_season_id_in_url(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(req):
            captured_urls.append(req.full_url if hasattr(req, "full_url") else str(req))
            return _mock_resp(b"<select></select>")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            AthleteOneClient().get_event_ids_for_season(69)

        # Assert
        assert "69" in captured_urls[0]


class TestAthleteOneClientFlightIds:
    def test_get_flight_ids_returns_list(self) -> None:
        # Arrange
        payload = json.dumps(_FLIGHT_IDS_PAYLOAD).encode()
        with patch("urllib.request.urlopen", return_value=_mock_resp(payload)):
            # Act
            result = AthleteOneClient().get_flight_ids_for_event(3925)

        # Assert
        assert isinstance(result, list)

    def test_get_flight_ids_extracts_girls_flights(self) -> None:
        # Arrange
        payload = json.dumps(_FLIGHT_IDS_PAYLOAD).encode()
        with patch("urllib.request.urlopen", return_value=_mock_resp(payload)):
            # Act
            result = AthleteOneClient().get_flight_ids_for_event(3925)

        # Assert
        assert 32626 in result
        assert 32624 in result

    def test_get_flight_ids_includes_boys_flights(self) -> None:
        # Arrange — boys events have boysDivAndFlightList populated instead
        payload_with_boys = {
            "result": "success",
            "data": {
                "girlsDivAndFlightList": [],
                "boysDivAndFlightList": [
                    {
                        "divisionID": 18600,
                        "divisionName": "B2013",
                        "flightList": [
                            {
                                "divisionID": 18600,
                                "flightID": 32700,
                                "flightName": "ECNL",
                                "teamsCount": 8,
                                "hasActiveSchedule": True,
                                "hideSettings": 0,
                            }
                        ],
                    }
                ],
            },
        }
        payload = json.dumps(payload_with_boys).encode()
        with patch("urllib.request.urlopen", return_value=_mock_resp(payload)):
            # Act
            result = AthleteOneClient().get_flight_ids_for_event(3930)

        # Assert
        assert 32700 in result

    def test_get_flight_ids_empty_divisions_returns_empty_list(self) -> None:
        # Arrange
        payload = json.dumps(
            {"result": "success", "data": {"girlsDivAndFlightList": [], "boysDivAndFlightList": []}}
        ).encode()
        with patch("urllib.request.urlopen", return_value=_mock_resp(payload)):
            # Act
            result = AthleteOneClient().get_flight_ids_for_event(9999)

        # Assert
        assert result == []

    def test_get_flight_ids_includes_event_id_in_url(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(req):
            captured_urls.append(req.full_url if hasattr(req, "full_url") else str(req))
            return _mock_resp(
                json.dumps(
                    {
                        "result": "success",
                        "data": {"girlsDivAndFlightList": [], "boysDivAndFlightList": []},
                    }
                ).encode()
            )

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            AthleteOneClient().get_flight_ids_for_event(3925)

        # Assert
        assert "3925" in captured_urls[0]


class TestAthleteOneClientSchedules:
    def test_get_schedules_returns_list(self) -> None:
        # Arrange
        payload = json.dumps(_SCHEDULES_PAYLOAD).encode()
        with patch("urllib.request.urlopen", return_value=_mock_resp(payload)):
            # Act
            result = AthleteOneClient().get_schedules_by_flight(3925, 32626)

        # Assert
        assert isinstance(result, list)

    def test_get_schedules_returns_all_matches(self) -> None:
        # Arrange
        payload = json.dumps(_SCHEDULES_PAYLOAD).encode()
        with patch("urllib.request.urlopen", return_value=_mock_resp(payload)):
            # Act
            result = AthleteOneClient().get_schedules_by_flight(3925, 32626)

        # Assert
        assert len(result) == 2

    def test_get_schedules_includes_event_and_flight_in_url(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(req):
            captured_urls.append(req.full_url if hasattr(req, "full_url") else str(req))
            return _mock_resp(json.dumps({"result": "success", "data": []}).encode())

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            AthleteOneClient().get_schedules_by_flight(3925, 32626)

        # Assert
        assert "3925" in captured_urls[0]
        assert "32626" in captured_urls[0]

    def test_get_schedules_empty_data_returns_empty_list(self) -> None:
        # Arrange
        payload = json.dumps({"result": "success", "data": []}).encode()
        with patch("urllib.request.urlopen", return_value=_mock_resp(payload)):
            # Act
            result = AthleteOneClient().get_schedules_by_flight(3925, 99999)

        # Assert
        assert result == []
