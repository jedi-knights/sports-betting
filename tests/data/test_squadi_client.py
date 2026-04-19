"""Tests for the Squadi API client."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from bet.data.squadi import SquadiClient

_COMPETITION_PAYLOAD = [
    {
        "id": 79,
        "uniqueKey": "b731b602-c560-43a0-9ec0-19f633ddc516",
        "name": "WPSL 2025",
        "yearRefId": 7,
        "organisationId": 157,
        "statusRefId": 2,
    },
    {
        "id": 80,
        "uniqueKey": "some-other-key",
        "name": "WPSL Division II 2025",
        "yearRefId": 7,
        "organisationId": 157,
        "statusRefId": 2,
    },
]

_MATCH_1 = {
    "id": 21914,
    "startTime": "2025-05-11T01:00:00.000Z",
    "endTime": "2025-05-11T03:42:09.000Z",
    "matchStatus": "ENDED",
    "team1Score": 0,
    "team2Score": 4,
    "team1": {"id": 10877, "name": "City SC Utah"},
    "team2": {"id": 10878, "name": "Utah Surf"},
}

_MATCH_2 = {
    "id": 21918,
    "startTime": "2025-05-14T00:00:00.000Z",
    "endTime": "2025-05-14T02:00:00.000Z",
    "matchStatus": "ENDED",
    "team1Score": 0,
    "team2Score": 6,
    "team1": {"id": 10880, "name": "Griffins FC"},
    "team2": {"id": 10878, "name": "Utah Surf"},
}

_ROUND_MATCHES_PAYLOAD = {
    "rounds": [
        {
            "id": 5852,
            "name": "Week One",
            "matches": [_MATCH_1],
        },
        {
            "id": 5853,
            "name": "Week Two",
            "matches": [_MATCH_2],
        },
        {
            "id": 5854,
            "name": "Week Three",
            "matches": [],
        },
    ],
    "allRoundsHidden": False,
}


def _mock_resp(payload) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestSquadiClientCompetitions:
    def test_get_competitions_returns_list(self) -> None:
        # Arrange
        with patch("urllib.request.urlopen", return_value=_mock_resp(_COMPETITION_PAYLOAD)):
            client = SquadiClient()

            # Act
            result = client.get_competitions("4257ebc9", year_ref_id=7)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_competitions_includes_org_key_in_url(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(req):
            captured_urls.append(req.full_url if hasattr(req, "full_url") else str(req))
            return _mock_resp([])

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            SquadiClient().get_competitions("my-org-key", year_ref_id=7)

        # Assert
        assert "my-org-key" in captured_urls[0]

    def test_get_competitions_includes_year_ref_id_in_url(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(req):
            captured_urls.append(req.full_url if hasattr(req, "full_url") else str(req))
            return _mock_resp([])

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            SquadiClient().get_competitions("key", year_ref_id=7)

        # Assert
        assert "yearRefId=7" in captured_urls[0]

    def test_get_competitions_sends_user_agent_header(self) -> None:
        # Arrange — bare urllib without User-Agent returns empty body; must be set
        captured_headers: list[dict] = []

        def fake_urlopen(req):
            captured_headers.append(dict(req.headers))
            return _mock_resp([])

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            SquadiClient().get_competitions("key", year_ref_id=7)

        # Assert
        assert "User-agent" in captured_headers[0]


class TestSquadiClientMatches:
    def test_get_matches_returns_flat_list(self) -> None:
        # Arrange
        with patch("urllib.request.urlopen", return_value=_mock_resp(_ROUND_MATCHES_PAYLOAD)):
            client = SquadiClient()

            # Act
            result = client.get_matches(competition_id=79)

        # Assert
        assert isinstance(result, list)

    def test_get_matches_flattens_rounds(self) -> None:
        # Arrange — two non-empty rounds should produce a single flat list of 2 matches
        with patch("urllib.request.urlopen", return_value=_mock_resp(_ROUND_MATCHES_PAYLOAD)):
            result = SquadiClient().get_matches(competition_id=79)

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 21914
        assert result[1]["id"] == 21918

    def test_get_matches_skips_empty_rounds(self) -> None:
        # Arrange — the third round has no matches and must not add empty entries
        with patch("urllib.request.urlopen", return_value=_mock_resp(_ROUND_MATCHES_PAYLOAD)):
            result = SquadiClient().get_matches(competition_id=79)

        # Assert
        assert all(isinstance(m, dict) for m in result)

    def test_get_matches_includes_competition_id_in_url(self) -> None:
        # Arrange
        captured_urls: list[str] = []

        def fake_urlopen(req):
            captured_urls.append(req.full_url if hasattr(req, "full_url") else str(req))
            return _mock_resp({"rounds": [], "allRoundsHidden": False})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            SquadiClient().get_matches(competition_id=79)

        # Assert
        assert "competitionId=79" in captured_urls[0]

    def test_get_matches_empty_rounds_returns_empty_list(self) -> None:
        # Arrange
        payload = {"rounds": [], "allRoundsHidden": False}
        with patch("urllib.request.urlopen", return_value=_mock_resp(payload)):
            result = SquadiClient().get_matches(competition_id=79)

        # Assert
        assert result == []
