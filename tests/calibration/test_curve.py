"""Tests for calibration curve (reliability diagram) generation."""

from __future__ import annotations

import pytest

from bet.calibration.curve import CalibrationCurve, calibration_curve


class TestCalibrationCurve:
    def test_returns_calibration_curve(self) -> None:
        probs = [0.1, 0.5, 0.9]
        outcomes = [0, 1, 1]
        result = calibration_curve(probs, outcomes)
        assert isinstance(result, CalibrationCurve)

    def test_empty_bins_are_omitted(self) -> None:
        # All probs in one bin — only one non-empty bin
        probs = [0.1, 0.15, 0.12]
        outcomes = [0, 1, 0]
        result = calibration_curve(probs, outcomes, n_bins=10)
        assert len(result.bin_centers) == 1

    def test_bin_counts_sum_to_n(self) -> None:
        probs = [0.1, 0.3, 0.5, 0.7, 0.9]
        outcomes = [0, 0, 1, 1, 1]
        result = calibration_curve(probs, outcomes)
        assert sum(result.bin_counts) == len(probs)

    def test_list_lengths_are_consistent(self) -> None:
        probs = [0.2, 0.4, 0.6, 0.8]
        outcomes = [0, 1, 1, 1]
        result = calibration_curve(probs, outcomes)
        n = len(result.bin_centers)
        assert len(result.observed_frequencies) == n
        assert len(result.bin_counts) == n

    def test_bin_centers_in_ascending_order(self) -> None:
        probs = [0.1, 0.5, 0.9]
        outcomes = [0, 1, 1]
        result = calibration_curve(probs, outcomes)
        assert result.bin_centers == sorted(result.bin_centers)

    def test_observed_frequencies_in_zero_one_range(self) -> None:
        probs = [0.2, 0.5, 0.8]
        outcomes = [0, 1, 1]
        result = calibration_curve(probs, outcomes)
        for freq in result.observed_frequencies:
            assert 0.0 <= freq <= 1.0

    def test_perfect_calibration_centers_equal_frequencies(self) -> None:
        # 10 games with prob=0.6; 6 win → center ≈ 0.6, frequency = 0.6
        probs = [0.6] * 10
        outcomes = [1] * 6 + [0] * 4
        result = calibration_curve(probs, outcomes)
        assert len(result.bin_centers) == 1
        assert abs(result.bin_centers[0] - 0.6) < 1e-9
        assert abs(result.observed_frequencies[0] - 0.6) < 1e-9

    def test_boundary_probability_one_is_included(self) -> None:
        probs = [1.0]
        outcomes = [1]
        result = calibration_curve(probs, outcomes)
        assert len(result.bin_centers) == 1

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            calibration_curve([], [])

    def test_mismatched_length_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            calibration_curve([0.5], [1, 0])
