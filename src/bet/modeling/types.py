"""Core data types for the Statistical Modeling context.

These types flow between the feature extractor, model, and calibration layers.
No type here knows about bookmakers, odds, or money.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FeatureSet:
    """Numerical features for one game as of a specific cutoff timestamp.

    The as_of field is a hard lookahead guard — the feature extractor must
    ensure no feature is derived from data recorded after this timestamp.

    Args:
        event_id: Identifier matching the Market Data event.
        sport: Sport key (e.g., ``"nfl"``, ``"soccer"``).
        home_team: Home team identifier.
        away_team: Away team identifier.
        as_of: Cutoff datetime; no future data may leak past this point.
        features: Sport-specific numerical features keyed by name.
    """

    event_id: str
    sport: str
    home_team: str
    away_team: str
    as_of: datetime
    features: dict[str, float] = field(default_factory=dict)


@dataclass
class ActualOutcome:
    """Final score for a completed game.

    Args:
        event_id: Identifier matching the Market Data event.
        home_score: Goals / points scored by the home team.
        away_score: Goals / points scored by the away team.
        final_at: Timestamp when the result became official.
    """

    event_id: str
    home_score: int
    away_score: int
    final_at: datetime


@dataclass
class TrainingExample:
    """Pairs a feature set with its known outcome for supervised training.

    Args:
        feature_set: Input features computed as of the game's kickoff time.
        outcome: Actual result used as the training label.
    """

    feature_set: FeatureSet
    outcome: ActualOutcome


@dataclass
class ProbabilityEstimate:
    """Model-predicted win probabilities for one game.

    ``home_win + away_win + (draw or 0) == 1.0`` is enforced on construction.
    ``draw`` is ``None`` for sports without a draw outcome (NFL, NBA, MLB, NHL).

    Args:
        event_id: Identifier matching the Market Data event.
        model_id: Name of the model that produced this estimate.
        generated_at: Timestamp when the estimate was produced.
        home_win: Probability the home team wins.
        away_win: Probability the away team wins.
        draw: Probability of a draw, or ``None`` for binary-outcome sports.

    Raises:
        ValueError: If the probabilities do not sum to 1.0 within 1e-6.
    """

    event_id: str
    model_id: str
    generated_at: datetime
    home_win: float
    away_win: float
    draw: float | None = None

    def __post_init__(self) -> None:
        draw = self.draw if self.draw is not None else 0.0
        total = self.home_win + self.away_win + draw
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"probabilities must sum to 1.0, got {total:.8f} "
                f"(home_win={self.home_win}, away_win={self.away_win}, "
                f"draw={self.draw})"
            )


def _outcome_label(home_score: int, away_score: int) -> str:
    """Return the string outcome label for a game result.

    Args:
        home_score: Goals / points scored by the home team.
        away_score: Goals / points scored by the away team.

    Returns:
        ``"home_win"``, ``"away_win"``, or ``"draw"``.
    """
    if home_score > away_score:
        return "home_win"
    if home_score < away_score:
        return "away_win"
    return "draw"
