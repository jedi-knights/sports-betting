"""Tests for isotonic regression calibrator."""

from __future__ import annotations

import pytest
from sklearn.exceptions import NotFittedError

from bet.calibration.isotonic import IsotonicCalibrator


def _overconfident_data() -> tuple[list[float], list[int]]:
    """Model predicts 0.8 but true win rate is 50%."""
    probs = [0.8] * 20
    outcomes = [1, 0] * 10
    return probs, outcomes


class TestIsotonicCalibratorFit:
    def test_fit_empty_raises(self) -> None:
        cal = IsotonicCalibrator()
        with pytest.raises(ValueError, match="fit requires"):
            cal.fit([], [])

    def test_fit_mismatched_length_raises(self) -> None:
        cal = IsotonicCalibrator()
        with pytest.raises(ValueError, match="same length"):
            cal.fit([0.5, 0.6], [1])

    def test_fit_succeeds_with_valid_data(self) -> None:
        cal = IsotonicCalibrator()
        probs, outcomes = _overconfident_data()
        cal.fit(probs, outcomes)  # should not raise


class TestIsotonicCalibratorTransform:
    def test_transform_before_fit_raises(self) -> None:
        cal = IsotonicCalibrator()
        with pytest.raises(NotFittedError):
            cal.transform([0.5])

    def test_output_in_zero_one_range(self) -> None:
        cal = IsotonicCalibrator()
        probs, outcomes = _overconfident_data()
        cal.fit(probs, outcomes)
        result = cal.transform([0.1, 0.5, 0.9])
        for p in result:
            assert 0.0 <= p <= 1.0

    def test_output_length_matches_input(self) -> None:
        cal = IsotonicCalibrator()
        probs, outcomes = _overconfident_data()
        cal.fit(probs, outcomes)
        result = cal.transform([0.2, 0.5, 0.8])
        assert len(result) == 3

    def test_overconfident_model_pulled_toward_base_rate(self) -> None:
        cal = IsotonicCalibrator()
        probs, outcomes = _overconfident_data()
        cal.fit(probs, outcomes)
        calibrated = cal.transform([0.8])[0]
        assert calibrated < 0.8

    def test_out_of_bounds_values_are_clipped(self) -> None:
        # transform should not raise for values outside training range
        cal = IsotonicCalibrator()
        probs = [0.3, 0.4, 0.5, 0.6, 0.7]
        outcomes = [0, 0, 1, 1, 1]
        cal.fit(probs, outcomes)
        result = cal.transform([0.0, 1.0])
        for p in result:
            assert 0.0 <= p <= 1.0

    def test_output_non_decreasing_for_sorted_input(self) -> None:
        cal = IsotonicCalibrator()
        probs = [0.2, 0.4, 0.6, 0.8]
        outcomes = [0, 0, 1, 1]
        cal.fit(probs, outcomes)
        result = cal.transform([0.1, 0.3, 0.5, 0.7, 0.9])
        for a, b in zip(result, result[1:], strict=False):
            assert b >= a
