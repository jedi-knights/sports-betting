"""Walk-forward backtesting pipeline."""

from __future__ import annotations

from ..modeling.protocols import Model
from ..modeling.types import ActualOutcome, FeatureSet, TrainingExample
from ..sizing.protocols import Sizer
from ..tracking.types import BetResult
from ..value.detector import MinimumEdgeDetector
from ..value.types import MarketLine
from .guard import assert_no_lookahead
from .types import HistoricalGame


class BacktestPipeline:
    """Runs walk-forward validation across a list of historical games.

    For each game treated as the test event, the pipeline:
    1. Selects all games that concluded strictly before the test game as training data.
    2. Asserts no lookahead bias in the training set.
    3. Fits the model on the training data.
    4. Extracts features for the test game.
    5. Generates a probability estimate.
    6. Detects value bets against the game's opening odds.
    7. Sizes each value bet via the configured Sizer.
    8. Resolves each bet against the actual score.
    9. Computes CLV against the closing line.

    Args:
        model: Any Model-protocol object. If it exposes ``fit_calibrator``,
            the pipeline will calibrate using the last ``calibration_fraction``
            of training games as a held-out calibration set.
        extractor: Feature extractor matching the sport and model.
        detector: ValueDetector that filters positive-EV opportunities.
        sizer: Sizer that computes stake from edge, odds, and bankroll.
        bankroll: Starting bankroll used for stake calculation.
        min_train_games: Minimum number of training games required before
            predictions are made. Games that would require fewer training
            examples are skipped.
        calibration_fraction: Fraction of training data held out for
            calibration when the model supports ``fit_calibrator``.
    """

    def __init__(
        self,
        model: Model,
        extractor: object,
        detector: MinimumEdgeDetector,
        sizer: Sizer,
        bankroll: float = 1000.0,
        min_train_games: int = 20,
        calibration_fraction: float = 0.2,
    ) -> None:
        self._model = model
        self._extractor = extractor
        self._detector = detector
        self._sizer = sizer
        self._bankroll = bankroll
        self._min_train_games = min_train_games
        self._calibration_fraction = calibration_fraction

    def run(self, games: list[HistoricalGame]) -> list[BetResult]:
        """Execute walk-forward validation and return all resolved bet outcomes.

        Args:
            games: All historical games for the backtest period. Order does
                not matter — they are sorted by game_date internally.

        Returns:
            One BetResult per detected value bet, in chronological order.
        """
        sorted_games = sorted(games, key=lambda g: g.game_date)
        results: list[BetResult] = []

        for test_game in sorted_games:
            train_games = [g for g in sorted_games if g.game_date < test_game.game_date]
            if len(train_games) < self._min_train_games:
                continue

            assert_no_lookahead(train_games, test_game.game_date)

            train_examples = [_to_training_example(g) for g in train_games]

            try:
                self._fit(train_games, train_examples)
            except Exception:
                continue

            try:
                features = self._extractor.extract(  # type: ignore[union-attr]
                    test_game.event_id,
                    test_game.home_team,
                    test_game.away_team,
                    as_of=test_game.game_date,
                )
            except Exception:
                continue

            try:
                estimate = self._model.predict(features)
            except Exception:
                continue

            lines = _to_market_lines(test_game)
            value_bets = self._detector.detect(estimate, lines)

            for vbet in value_bets:
                sizing = self._sizer.size(vbet.edge, vbet.decimal_odds, self._bankroll)
                won = _bet_won(vbet.side, test_game)
                pnl = sizing.stake * (vbet.decimal_odds - 1.0) if won else -sizing.stake
                clv = _compute_clv(vbet.side, vbet.decimal_odds, test_game)
                results.append(
                    BetResult(
                        bet_id=f"{test_game.event_id}_{vbet.side}",
                        stake=sizing.stake,
                        decimal_odds=vbet.decimal_odds,
                        model_prob=vbet.model_prob,
                        edge=vbet.edge,
                        won=won,
                        pnl=pnl,
                        clv=clv,
                    )
                )

        return results

    def _fit(
        self,
        train_games: list[HistoricalGame],
        train_examples: list[TrainingExample],
    ) -> None:
        if not hasattr(self._model, "fit_calibrator"):
            self._model.fit(train_examples)
            self._extractor.fit(train_examples)  # type: ignore[union-attr]
            return

        split = max(1, int(len(train_examples) * (1.0 - self._calibration_fraction)))
        fit_examples = train_examples[:split]
        cal_games = train_games[split:]

        self._model.fit(fit_examples)
        self._extractor.fit(fit_examples)  # type: ignore[union-attr]

        if not cal_games:
            return

        probs: list[float] = []
        outcomes: list[int] = []
        for cal_game in cal_games:
            earlier = [
                e for e in fit_examples if e.feature_set.as_of < cal_game.game_date
            ]
            if not earlier:
                continue
            try:
                self._extractor.fit(earlier)  # type: ignore[union-attr]
                fs = self._extractor.extract(  # type: ignore[union-attr]
                    cal_game.event_id,
                    cal_game.home_team,
                    cal_game.away_team,
                    as_of=cal_game.game_date,
                )
                raw = self._model.predict_raw(fs)  # type: ignore[union-attr]
                probs.append(raw.home_win)
                outcomes.append(1 if cal_game.home_score > cal_game.away_score else 0)
            except Exception:
                continue

        if len(probs) >= 2:
            self._model.fit_calibrator(probs, outcomes)  # type: ignore[union-attr]


def _to_training_example(game: HistoricalGame) -> TrainingExample:
    return TrainingExample(
        feature_set=FeatureSet(
            event_id=game.event_id,
            sport=game.sport,
            home_team=game.home_team,
            away_team=game.away_team,
            as_of=game.game_date,
            features={},
        ),
        outcome=ActualOutcome(
            event_id=game.event_id,
            home_score=game.home_score,
            away_score=game.away_score,
            final_at=game.game_date,
        ),
    )


def _to_market_lines(game: HistoricalGame) -> list[MarketLine]:
    lines = [
        MarketLine(
            market_id=game.event_id,
            side="home_win",
            decimal_odds=game.home_win_odds,
            implied_prob=1.0 / game.home_win_odds,
        ),
        MarketLine(
            market_id=game.event_id,
            side="away_win",
            decimal_odds=game.away_win_odds,
            implied_prob=1.0 / game.away_win_odds,
        ),
    ]
    if game.draw_odds is not None:
        lines.append(
            MarketLine(
                market_id=game.event_id,
                side="draw",
                decimal_odds=game.draw_odds,
                implied_prob=1.0 / game.draw_odds,
            )
        )
    return lines


def _bet_won(side: str, game: HistoricalGame) -> bool:
    if side == "home_win":
        return game.home_score > game.away_score
    if side == "away_win":
        return game.away_score > game.home_score
    if side == "draw":
        return game.home_score == game.away_score
    return False


def _compute_clv(side: str, bet_odds: float, game: HistoricalGame) -> float | None:
    if side == "home_win":
        closing = game.closing_home_win_odds
    elif side == "away_win":
        closing = game.closing_away_win_odds
    elif side == "draw":
        closing = game.closing_draw_odds
    else:
        return None
    if closing is None:
        return None
    return 1.0 / closing - 1.0 / bet_odds
