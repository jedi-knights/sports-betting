"""Tests for the `bet fetch` CLI command."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from bet.backtesting.types import HistoricalGame
from bet.cli import main

_GAME = HistoricalGame(
    event_id="ecnl_906430",
    sport="ecnl_girls",
    home_team="NCFC Youth ECNL G13",
    away_team="Charlotte SA ECNL G13",
    game_date=datetime(2025, 9, 6, 10, 0, 0, tzinfo=UTC),
    home_score=1,
    away_score=3,
    home_win_odds=None,
    away_win_odds=None,
    draw_odds=None,
    closing_home_win_odds=None,
    closing_away_win_odds=None,
    closing_draw_odds=None,
)

_MLS_GAME = HistoricalGame(
    event_id="mls_abc123",
    sport="mls",
    home_team="LA Galaxy",
    away_team="LAFC",
    game_date=datetime(2024, 3, 15, 20, 0, 0, tzinfo=UTC),
    home_score=2,
    away_score=1,
    home_win_odds=None,
    away_win_odds=None,
    draw_odds=None,
    closing_home_win_odds=None,
    closing_away_win_odds=None,
    closing_draw_odds=None,
)


def _patched_ecnl_fetcher(games: list[HistoricalGame]) -> MagicMock:
    mock = MagicMock()
    mock.return_value.fetch.return_value = games
    return mock


class TestFetchCommandBasics:
    def test_fetch_command_exists(self) -> None:
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(main, ["fetch", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "league" in result.output.lower()

    def test_fetch_exits_zero_on_success(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_GAME]

            # Act
            result = runner.invoke(
                main, ["fetch", "--league", "ecnl-girls", "--output", str(output)]
            )

        # Assert
        assert result.exit_code == 0

    def test_fetch_reports_game_count(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_GAME]

            # Act
            result = runner.invoke(
                main, ["fetch", "--league", "ecnl-girls", "--output", str(output)]
            )

        # Assert
        assert "1" in result.output

    def test_fetch_reports_output_path(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_GAME]

            # Act
            result = runner.invoke(
                main, ["fetch", "--league", "ecnl-girls", "--output", str(output)]
            )

        # Assert
        assert str(output) in result.output


class TestFetchCommandCsvOutput:
    def test_writes_csv_file(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "ecnl.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_GAME]

            # Act
            runner.invoke(main, ["fetch", "--league", "ecnl-girls", "--output", str(output)])

        # Assert
        assert output.exists()

    def test_csv_has_correct_headers(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "ecnl.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_GAME]
            runner.invoke(main, ["fetch", "--league", "ecnl-girls", "--output", str(output)])

        # Act
        with output.open() as f:
            headers = csv.DictReader(f).fieldnames

        # Assert
        assert "event_id" in headers
        assert "sport" in headers
        assert "home_team" in headers
        assert "away_team" in headers
        assert "game_date" in headers
        assert "home_score" in headers
        assert "away_score" in headers

    def test_csv_contains_game_data(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "ecnl.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_GAME]
            runner.invoke(main, ["fetch", "--league", "ecnl-girls", "--output", str(output)])

        # Act
        with output.open() as f:
            rows = list(csv.DictReader(f))

        # Assert
        assert len(rows) == 1
        assert rows[0]["event_id"] == "ecnl_906430"
        assert rows[0]["sport"] == "ecnl_girls"
        assert rows[0]["home_team"] == "NCFC Youth ECNL G13"
        assert rows[0]["home_score"] == "1"
        assert rows[0]["away_score"] == "3"

    def test_csv_game_date_is_iso_format(self, tmp_path: Path) -> None:
        # Arrange — CSVDataLoader reads game_date via fromisoformat
        runner = CliRunner()
        output = tmp_path / "ecnl.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_GAME]
            runner.invoke(main, ["fetch", "--league", "ecnl-girls", "--output", str(output)])

        # Act
        with output.open() as f:
            rows = list(csv.DictReader(f))

        # Assert — must be parseable by fromisoformat
        parsed = datetime.fromisoformat(rows[0]["game_date"])
        assert parsed.year == 2025
        assert parsed.month == 9
        assert parsed.day == 6

    def test_csv_none_odds_written_as_empty_string(self, tmp_path: Path) -> None:
        # Arrange — CSVDataLoader reads empty string as None for odds fields
        runner = CliRunner()
        output = tmp_path / "ecnl.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_GAME]
            runner.invoke(main, ["fetch", "--league", "ecnl-girls", "--output", str(output)])

        # Act
        with output.open() as f:
            rows = list(csv.DictReader(f))

        # Assert
        assert rows[0]["home_win_odds"] == ""
        assert rows[0]["away_win_odds"] == ""


class TestFetchCommandDefaultOutput:
    def test_default_output_derived_from_league(self, tmp_path: Path) -> None:
        # Arrange — if --output is omitted, file should be <league>.csv in cwd
        runner = CliRunner()

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_GAME]

            # Act — run inside tmp_path so the default file lands there
            with runner.isolated_filesystem(temp_dir=tmp_path):
                result = runner.invoke(main, ["fetch", "--league", "ecnl-girls"])
                output = Path("ecnl-girls.csv")

                # Assert
                assert result.exit_code == 0
                assert output.exists()


class TestFetchCommandLeagues:
    def test_ecnl_girls_uses_ecnl_data_fetcher(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = []

            # Act
            runner.invoke(main, ["fetch", "--league", "ecnl-girls", "--output", str(output)])

        # Assert
        mock_cls.assert_called_once()

    def test_ecnl_boys_uses_ecnl_data_fetcher(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = []

            # Act
            runner.invoke(main, ["fetch", "--league", "ecnl-boys", "--output", str(output)])

        # Assert
        mock_cls.assert_called_once()

    def test_nwsl_uses_nwsl_data_fetcher(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.NWSLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = []

            # Act
            runner.invoke(main, ["fetch", "--league", "nwsl", "--output", str(output)])

        # Assert
        mock_cls.assert_called_once()

    def test_mls_uses_mls_data_fetcher(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.MLSDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = [_MLS_GAME]

            # Act
            runner.invoke(main, ["fetch", "--league", "mls", "--output", str(output)])

        # Assert
        mock_cls.assert_called_once()

    def test_wpsl_uses_wpsl_data_fetcher(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.WPSLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = []

            # Act
            runner.invoke(main, ["fetch", "--league", "wpsl", "--output", str(output)])

        # Assert
        mock_cls.assert_called_once()


class TestFetchCommandHistoryFlag:
    def test_history_flag_passes_all_ecnl_girls_season_ids(self, tmp_path: Path) -> None:
        # Arrange
        from bet.data.ecnl import ECNL_GIRLS_SEASON_IDS

        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = []

            # Act
            runner.invoke(
                main,
                ["fetch", "--league", "ecnl-girls", "--history", "--output", str(output)],
            )

        # Assert
        _, kwargs = mock_cls.call_args
        assert kwargs["season_ids"] == ECNL_GIRLS_SEASON_IDS

    def test_history_flag_passes_all_ecnl_boys_season_ids(self, tmp_path: Path) -> None:
        # Arrange
        from bet.data.ecnl import ECNL_BOYS_SEASON_IDS

        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = []

            # Act
            runner.invoke(
                main,
                ["fetch", "--league", "ecnl-boys", "--history", "--output", str(output)],
            )

        # Assert
        _, kwargs = mock_cls.call_args
        assert kwargs["season_ids"] == ECNL_BOYS_SEASON_IDS

    def test_no_history_flag_uses_current_season_for_ecnl_girls(self, tmp_path: Path) -> None:
        # Arrange
        runner = CliRunner()
        output = tmp_path / "out.csv"

        with patch("bet.cli.ECNLDataFetcher") as mock_cls:
            mock_cls.return_value.fetch.return_value = []

            # Act
            runner.invoke(main, ["fetch", "--league", "ecnl-girls", "--output", str(output)])

        # Assert — current season only (69 = ECNL Girls 2025-26)
        _, kwargs = mock_cls.call_args
        assert kwargs["season_ids"] == [69]
