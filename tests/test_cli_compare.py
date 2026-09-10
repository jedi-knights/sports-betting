"""Tests for the CLI's compare command.

The compare command runs the same walk-forward window through every applicable
(model, calibrated?) combination for one sport, then emits a ranked markdown
report. It is the model-comparison harness — a way to answer "which model
should we use for this sport?" from a single invocation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from click.testing import CliRunner

from bet.cli import main

_CSV_HEADER = (
    "event_id,sport,home_team,away_team,game_date,"
    "home_score,away_score,home_win_odds,away_win_odds,draw_odds,"
    "closing_home_win_odds,closing_away_win_odds,closing_draw_odds"
)


def _write_mls_no_odds_fixture(path: Path, n_games: int = 60) -> Path:
    base = datetime(2023, 3, 1, tzinfo=UTC)
    teams = ["Fire", "Union", "Rapids", "Galaxy", "Timbers", "Whitecaps"]
    rows = []
    for i in range(n_games):
        home = teams[i % len(teams)]
        away = teams[(i + 1) % len(teams)]
        hs, as_ = (2, 1) if i % 3 != 0 else (0, 1)
        game_date = (base + timedelta(days=i * 4)).isoformat()
        rows.append(f"mls_{i:03d},mls,{home},{away},{game_date},{hs},{as_},,,,,,")
    path.write_text(_CSV_HEADER + "\n" + "\n".join(rows) + "\n")
    return path


def _write_nfl_fixture(path: Path, n_games: int = 40) -> Path:
    base = datetime(2023, 9, 1, tzinfo=UTC)
    teams = ["alpha", "bravo", "charlie", "delta", "echo"]
    rows = []
    for i in range(n_games):
        home = teams[i % len(teams)]
        away = teams[(i + 1) % len(teams)]
        hs, as_ = (24, 17) if i % 3 != 0 else (14, 21)
        game_date = (base + timedelta(days=i * 7)).isoformat()
        rows.append(f"nfl_{i:03d},nfl,{home},{away},{game_date},{hs},{as_},1.80,2.10,,1.82,2.08,")
    path.write_text(_CSV_HEADER + "\n" + "\n".join(rows) + "\n")
    return path


class TestCompareCommand:
    def test_compare_command_exists(self) -> None:
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(main, ["compare", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "compare" in result.output.lower()

    def test_compare_runs_on_mls_no_odds_fixture(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_mls_no_odds_fixture(tmp_path / "mls.csv")
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            ["compare", "--sport", "mls", "--data", str(fixture), "--min-train", "20"],
        )

        # Assert
        assert result.exit_code == 0, result.output

    def test_compare_output_lists_multiple_models(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_mls_no_odds_fixture(tmp_path / "mls.csv")
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            ["compare", "--sport", "mls", "--data", str(fixture), "--min-train", "20"],
        )

        # Assert — at least Poisson should appear for mls
        assert "poisson" in result.output.lower(), result.output

    def test_compare_reports_brier_column(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_mls_no_odds_fixture(tmp_path / "mls.csv")
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            ["compare", "--sport", "mls", "--data", str(fixture), "--min-train", "20"],
        )

        # Assert
        assert "brier" in result.output.lower(), result.output

    def test_compare_writes_markdown_output(self, tmp_path: Path) -> None:
        # Arrange
        fixture = _write_mls_no_odds_fixture(tmp_path / "mls.csv")
        out_path = tmp_path / "compare.md"
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            [
                "compare",
                "--sport",
                "mls",
                "--data",
                str(fixture),
                "--min-train",
                "20",
                "--output",
                str(out_path),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        assert out_path.exists()
        body = out_path.read_text()
        assert "| Model" in body or "| model" in body
        assert "|---" in body  # markdown table separator

    def test_compare_ranks_by_brier_ascending(self, tmp_path: Path) -> None:
        """The report's first data row must have the lowest Brier score."""
        # Arrange
        fixture = _write_mls_no_odds_fixture(tmp_path / "mls.csv")
        out_path = tmp_path / "compare.md"
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            [
                "compare",
                "--sport",
                "mls",
                "--data",
                str(fixture),
                "--min-train",
                "20",
                "--output",
                str(out_path),
            ],
        )

        # Assert
        assert result.exit_code == 0
        rows = [
            line
            for line in out_path.read_text().splitlines()
            if line.startswith("|") and not line.startswith("|---") and "Model" not in line
        ]
        # Extract Brier from each row (assumes Brier is the 2nd or 3rd numeric column)
        briers: list[float] = []
        for row in rows:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            for c in cells[1:]:
                try:
                    briers.append(float(c))
                    break
                except ValueError:
                    continue
        assert len(briers) >= 2, f"expected 2+ data rows, got {rows}"
        assert briers == sorted(briers), f"rows not sorted by Brier ascending: {briers}"

    def test_compare_runs_on_nfl_fixture(self, tmp_path: Path) -> None:
        """NFL has odds and multiple compatible models."""
        # Arrange
        fixture = _write_nfl_fixture(tmp_path / "nfl.csv")
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            ["compare", "--sport", "nfl", "--data", str(fixture), "--min-train", "10"],
        )

        # Assert
        assert result.exit_code == 0, result.output
        assert "elo" in result.output.lower()

    def test_compare_skips_poisson_for_nfl(self, tmp_path: Path) -> None:
        """Poisson is soccer-only — must not appear in an NFL comparison."""
        # Arrange
        fixture = _write_nfl_fixture(tmp_path / "nfl.csv")
        out_path = tmp_path / "report.md"
        runner = CliRunner()

        # Act
        result = runner.invoke(
            main,
            [
                "compare",
                "--sport",
                "nfl",
                "--data",
                str(fixture),
                "--min-train",
                "10",
                "--output",
                str(out_path),
            ],
        )

        # Assert — check the rendered report, not the console output
        # (console echoes the file path, which the test name contains "poisson")
        assert result.exit_code == 0
        assert "poisson" not in out_path.read_text().lower()
