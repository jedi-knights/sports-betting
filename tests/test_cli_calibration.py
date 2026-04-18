"""Tests for the CLI's calibration-wrapping helper and calibrate command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from bet.calibration.model import CalibratedModel
from bet.cli import main
from bet.modeling.elo import EloModel
from bet.modeling.logistic import LogisticRegressionModel


class TestMaybeCalibrate:
    def test_calibrate_true_wraps_in_calibrated_model(self) -> None:
        # Arrange
        from bet.cli import _maybe_calibrate

        model = EloModel()

        # Act
        result = _maybe_calibrate(model, calibrate=True)

        # Assert
        assert isinstance(result, CalibratedModel)

    def test_calibrate_false_returns_model_unchanged(self) -> None:
        # Arrange
        from bet.cli import _maybe_calibrate

        model = EloModel()

        # Act
        result = _maybe_calibrate(model, calibrate=False)

        # Assert
        assert result is model

    def test_wraps_any_model_type(self) -> None:
        # Arrange
        from bet.cli import _maybe_calibrate

        model = LogisticRegressionModel()

        # Act
        result = _maybe_calibrate(model, calibrate=True)

        # Assert
        assert isinstance(result, CalibratedModel)

    def test_wrapped_model_id_reflects_calibration(self) -> None:
        # Arrange
        from bet.cli import _maybe_calibrate

        model = EloModel()

        # Act
        result = _maybe_calibrate(model, calibrate=True)

        # Assert
        assert isinstance(result, CalibratedModel)
        assert "calibrated" in result.model_id

    def test_calibrate_default_is_true(self) -> None:
        # Arrange
        from bet.cli import _maybe_calibrate

        model = EloModel()

        # Act — call without explicit calibrate kwarg
        result = _maybe_calibrate(model)

        # Assert
        assert isinstance(result, CalibratedModel)


_CSV_HEADER = (
    "event_id,sport,home_team,away_team,game_date,"
    "home_score,away_score,home_win_odds,away_win_odds,draw_odds,"
    "closing_home_win_odds,closing_away_win_odds,closing_draw_odds"
)


def _write_nfl_fixture(path: Path, n_games: int = 40) -> Path:
    from datetime import UTC, datetime, timedelta

    base = datetime(2023, 9, 1, tzinfo=UTC)
    rows = []
    teams = ["alpha", "bravo", "charlie", "delta", "echo"]
    for i in range(n_games):
        home = teams[i % len(teams)]
        away = teams[(i + 1) % len(teams)]
        hs, as_ = (24, 17) if i % 3 != 0 else (14, 21)
        game_date = (base + timedelta(days=i * 7)).isoformat()
        rows.append(f"nfl_{i:03d},nfl,{home},{away},{game_date},{hs},{as_},1.80,2.10,,1.82,2.08,")
    path.write_text(_CSV_HEADER + "\n" + "\n".join(rows) + "\n")
    return path


class TestCalibrateCommand:
    def test_calibrate_command_exists(self) -> None:
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(main, ["calibrate", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "calibrate" in result.output.lower() or "brier" in result.output.lower()

    def test_calibrate_runs_on_nfl_fixture(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_nfl_fixture(tmp_path / "nfl.csv")
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            ["calibrate", "--sport", "nfl", "--data", str(fixture), "--model", "elo"],
        )

        # Assert
        assert result.exit_code == 0, result.output
        assert "Brier" in result.output

    def test_calibrate_reports_log_loss(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_nfl_fixture(tmp_path / "nfl.csv")
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            ["calibrate", "--sport", "nfl", "--data", str(fixture), "--model", "elo"],
        )

        # Assert
        assert result.exit_code == 0
        assert "Log loss" in result.output or "log_loss" in result.output.lower()

    def test_calibrate_exits_zero_on_success(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_nfl_fixture(tmp_path / "nfl.csv")
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            ["calibrate", "--sport", "nfl", "--data", str(fixture)],
        )

        # Assert
        assert result.exit_code == 0
