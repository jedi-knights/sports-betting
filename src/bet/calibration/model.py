"""CalibratedModel: wraps any Model with post-hoc probability calibration."""

from __future__ import annotations

from sklearn.exceptions import NotFittedError

from ..modeling.protocols import Model
from ..modeling.types import FeatureSet, ProbabilityEstimate, TrainingExample
from .protocols import Calibrator


class CalibratedModel:
    """Wraps any Model and applies post-hoc probability calibration on predict.

    Usage:

        model = CalibratedModel(EloModel(), PlattScaler())
        model.fit(train_examples)          # fits the inner model
        model.fit_calibrator(probs, outcomes)  # fits calibrator on held-out data
        estimate = model.predict(features)

    The calibrator corrects home_win probabilities; away_win and draw are
    renormalised proportionally so all three still sum to 1.

    Args:
        model: Any object satisfying the Model protocol.
        calibrator: Any object satisfying the Calibrator protocol.
    """

    def __init__(self, model: Model, calibrator: Calibrator) -> None:
        self._model = model
        self._calibrator = calibrator
        self._calibrator_fitted = False

    @property
    def model_id(self) -> str:
        """Identifier combining the inner model name and calibration method."""
        return f"{self._model.model_id}_calibrated"

    def fit(self, examples: list[TrainingExample]) -> None:
        """Fit the inner model.

        The calibrator must be fitted separately by calling fit_calibrator()
        before predict() can be used. This separation allows calibrating on
        a held-out validation set rather than the same training data.

        Args:
            examples: Labelled training examples passed directly to the inner model.
        """
        self._model.fit(examples)

    def fit_calibrator(self, probs: list[float], outcomes: list[int]) -> None:
        """Fit the calibration correction on held-out predictions and outcomes.

        Call this after fitting the inner model on separate training data.
        Pass the inner model's predictions on a validation set together with
        the true binary outcomes (1 = home win, 0 = not home win).

        Args:
            probs: Raw home_win probabilities from the inner model's predict().
            outcomes: Binary labels — 1 if home won, 0 otherwise.
        """
        self._calibrator.fit(probs, outcomes)
        self._calibrator_fitted = True

    def predict_raw(self, features: FeatureSet) -> ProbabilityEstimate:
        """Predict using the inner model without applying calibration.

        Useful when generating calibration inputs from a held-out validation
        set during walk-forward backtesting.

        Args:
            features: Feature set passed directly to the inner model.

        Returns:
            Uncalibrated ProbabilityEstimate from the inner model.
        """
        return self._model.predict(features)

    def predict(self, features: FeatureSet) -> ProbabilityEstimate:
        """Predict calibrated win probabilities.

        Calibrates the home_win probability, then renormalises away_win and
        draw proportionally so home_win + away_win + (draw or 0) == 1.

        Args:
            features: Feature set passed directly to the inner model.

        Returns:
            A ProbabilityEstimate with calibrated, normalised probabilities.

        Raises:
            NotFittedError: If fit_calibrator() has not been called.
        """
        if not self._calibrator_fitted:
            raise NotFittedError("call fit_calibrator() before predict()")

        raw = self._model.predict(features)
        calibrated_home = float(self._calibrator.transform([raw.home_win])[0])
        calibrated_home = max(0.0, min(1.0, calibrated_home))
        remaining = 1.0 - calibrated_home

        if raw.draw is None:
            away_win = remaining
            draw: float | None = None
        else:
            denom = raw.away_win + raw.draw
            if denom > 0.0:
                away_win = raw.away_win * remaining / denom
                draw = raw.draw * remaining / denom
            else:
                away_win = remaining / 2.0
                draw = remaining / 2.0

        return ProbabilityEstimate(
            event_id=features.event_id,
            model_id=self.model_id,
            generated_at=features.as_of,
            home_win=calibrated_home,
            away_win=away_win,
            draw=draw,
        )
