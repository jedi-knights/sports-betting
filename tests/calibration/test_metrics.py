"""Tests for calibration quality metrics."""

from __future__ import annotations

import math

import pytest

from bet.calibration.metrics import (
    brier_score,
    expected_calibration_error,
    log_loss,
)


class TestBrierScore:
    def test_perfect_predictions_give_zero(self) -> None:
        probs = [0.0, 1.0, 1.0, 0.0]
        outcomes = [0, 1, 1, 0]
        assert brier_score(probs, outcomes) == 0.0

    def test_worst_predictions_give_one(self) -> None:
        probs = [1.0, 0.0]
        outcomes = [0, 1]
        assert brier_score(probs, outcomes) == 1.0

    def test_random_guess_gives_quarter(self) -> None:
        probs = [0.5] * 100
        outcomes = [1, 0] * 50
        assert abs(brier_score(probs, outcomes) - 0.25) < 1e-9

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            brier_score([], [])

    def test_mismatched_length_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            brier_score([0.5, 0.5], [1])

    def test_result_in_zero_one_range(self) -> None:
        probs = [0.2, 0.4, 0.6, 0.8]
        outcomes = [0, 0, 1, 1]
        score = brier_score(probs, outcomes)
        assert 0.0 <= score <= 1.0


class TestLogLoss:
    def test_near_perfect_predictions_give_low_loss(self) -> None:
        probs = [0.99, 0.01, 0.99, 0.01]
        outcomes = [1, 0, 1, 0]
        assert log_loss(probs, outcomes) < 0.02

    def test_confident_wrong_predictions_give_high_loss(self) -> None:
        probs = [0.99, 0.99]
        outcomes = [0, 0]
        assert log_loss(probs, outcomes) > 4.0

    def test_does_not_crash_on_zero_probability(self) -> None:
        probs = [0.0, 1.0]
        outcomes = [0, 1]
        result = log_loss(probs, outcomes)
        assert math.isfinite(result)

    def test_does_not_crash_on_one_probability(self) -> None:
        probs = [1.0, 0.0]
        outcomes = [0, 1]
        result = log_loss(probs, outcomes)
        assert math.isfinite(result)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            log_loss([], [])

    def test_mismatched_length_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            log_loss([0.5], [1, 0])

    def test_result_non_negative(self) -> None:
        probs = [0.3, 0.7, 0.5]
        outcomes = [0, 1, 1]
        assert log_loss(probs, outcomes) >= 0.0


class TestExpectedCalibrationError:
    def test_perfect_calibration_gives_zero(self) -> None:
        # 10 predictions of 0.6, 6 win → observed 0.6 → ECE = 0
        probs = [0.6] * 10
        outcomes = [1] * 6 + [0] * 4
        assert abs(expected_calibration_error(probs, outcomes) - 0.0) < 1e-9

    def test_completely_wrong_calibration_gives_high_ece(self) -> None:
        # Predict 0.9 for every game but only 10% win
        probs = [0.9] * 10
        outcomes = [1] + [0] * 9
        ece = expected_calibration_error(probs, outcomes)
        assert ece > 0.5

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            expected_calibration_error([], [])

    def test_result_in_zero_one_range(self) -> None:
        probs = [0.1, 0.3, 0.5, 0.7, 0.9]
        outcomes = [0, 0, 1, 1, 1]
        ece = expected_calibration_error(probs, outcomes)
        assert 0.0 <= ece <= 1.0

    def test_boundary_probability_one_handled(self) -> None:
        probs = [1.0]
        outcomes = [1]
        ece = expected_calibration_error(probs, outcomes)
        assert ece == 0.0
