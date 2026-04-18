"""Tests for Platt scaling calibrator."""

from __future__ import annotations

import pytest
from sklearn.exceptions import NotFittedError

from bet.calibration.platt import PlattScaler


def _overconfident_data() -> tuple[list[float], list[int]]:
    """Model predicts 0.8 but true win rate is 50%."""
    probs = [0.8] * 20
    outcomes = [1, 0] * 10
    return probs, outcomes


class TestPlattScalerFit:
    def test_fit_empty_raises(self) -> None:
        scaler = PlattScaler()
        with pytest.raises(ValueError, match="fit requires"):
            scaler.fit([], [])

    def test_fit_mismatched_length_raises(self) -> None:
        scaler = PlattScaler()
        with pytest.raises(ValueError, match="same length"):
            scaler.fit([0.5, 0.6], [1])

    def test_fit_succeeds_with_valid_data(self) -> None:
        scaler = PlattScaler()
        probs, outcomes = _overconfident_data()
        scaler.fit(probs, outcomes)  # should not raise


class TestPlattScalerTransform:
    def test_transform_before_fit_raises(self) -> None:
        scaler = PlattScaler()
        with pytest.raises(NotFittedError):
            scaler.transform([0.5])

    def test_output_in_zero_one_range(self) -> None:
        scaler = PlattScaler()
        probs, outcomes = _overconfident_data()
        scaler.fit(probs, outcomes)
        result = scaler.transform([0.1, 0.5, 0.9])
        for p in result:
            assert 0.0 <= p <= 1.0

    def test_output_length_matches_input(self) -> None:
        scaler = PlattScaler()
        probs, outcomes = _overconfident_data()
        scaler.fit(probs, outcomes)
        result = scaler.transform([0.2, 0.5, 0.8])
        assert len(result) == 3

    def test_overconfident_model_pulled_toward_base_rate(self) -> None:
        # Raw prob 0.8 with 50% true win rate → calibrated should be < 0.8
        scaler = PlattScaler()
        probs, outcomes = _overconfident_data()
        scaler.fit(probs, outcomes)
        calibrated = scaler.transform([0.8])[0]
        assert calibrated < 0.8

    def test_monotonic_higher_input_gives_higher_output(self) -> None:
        # Platt scaling is logistic → strictly monotone
        scaler = PlattScaler()
        probs = [0.2] * 10 + [0.8] * 10
        outcomes = [0] * 10 + [1] * 10
        scaler.fit(probs, outcomes)
        low = scaler.transform([0.3])[0]
        high = scaler.transform([0.7])[0]
        assert high > low
