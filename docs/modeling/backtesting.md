# Backtesting

Backtesting is the process of evaluating a betting model against historical data to estimate how it would have performed if deployed in the past. It is the primary tool for validating a model before risking real money — but it is also one of the most commonly misused techniques in quantitative sports betting. This document covers the right way to do it and the pitfalls that produce falsely optimistic results.

## What Backtesting Measures

A backtest simulates the following process over historical data:

1. At the time of game `g`, use only information that would have been available before `g` to generate a probability estimate.
2. Compare that probability to the historical odds that were available at that time.
3. Simulate placing a bet if a positive-EV opportunity existed.
4. Record the outcome and update the bankroll.
5. Repeat across all games in the dataset.

The result is a simulated betting record: wins, losses, ROI, and bankroll trajectory over time.

## Walk-Forward Validation

The most important principle in backtesting is that your model must never see the future when making a prediction. Walk-forward validation enforces this:

1. Train the model on data from period T0 to T1.
2. Generate predictions for period T1 to T2 (the test window). Do not retrain during this window.
3. Advance the training window forward. Retrain on T0 to T2.
4. Generate predictions for T2 to T3.
5. Repeat until the full dataset is consumed.

This produces an out-of-sample prediction for every game in the dataset, simulating true deployment conditions.

**Why this matters**: If you train on all historical data and then evaluate on the same data, your model will appear far more accurate than it truly is. This is called in-sample testing and is nearly worthless for estimating real-world performance.

## Lookahead Bias: The Most Dangerous Pitfall

Lookahead bias occurs when your model or feature pipeline uses information that was not actually available at prediction time. It is easy to introduce accidentally and will produce results that look excellent in backtesting but fail completely in deployment.

Common sources of lookahead bias:

- **Final season statistics**: using a player's season averages computed at season end, rather than their rolling average up to that game date
- **Injury data**: using injury reports that were published after the game started
- **Line movements**: using the closing line as a model feature when you would only have had the opening line at prediction time
- **Score normalization**: normalizing team scoring using season-wide means computed after the season ended
- **Data leakage**: accidentally joining future results into a historical feature dataset

**Rule**: every feature used to predict game `g` must be computable using only data from games strictly before `g`.

## Realistic Odds Assumptions

A common mistake is backtesting against odds that were not actually available. Options in decreasing order of reliability:

1. **Historical opening odds**: available from odds history providers. Represents the price that was genuinely available before sharp action moved the line.
2. **Historical closing odds**: the price at game start. Often used as a proxy for market efficiency, but may not reflect what was actually bettable.
3. **Reconstructed odds**: estimated from point spreads using standard conversion formulas. Reasonable for spread markets, less reliable for moneylines.
4. **Assumed standard lines** (e.g., always `-110`): acceptable for spread/total markets in sports where this is truly standard, but eliminates any line-shopping benefit.

Never backtest using post-game odds or reconstructed odds without acknowledging the assumption.

## Bet Selection Logic

The backtest must implement the same bet selection rule you intend to use in production:

- **Minimum edge threshold**: only bet when model probability exceeds implied probability by at least X%
- **Kelly-based sizing**: bet size as a fraction of Kelly-recommended amount
- **Flat staking**: fixed bet size regardless of edge
- **Maximum exposure**: limits per game, per day, or per bankroll percentage

Testing with a different bet selection rule than you plan to deploy produces meaningless results.

## Key Metrics to Track

### ROI (Return on Investment)

```
ROI = (total_profit / total_amount_wagered) × 100%
```

The primary performance metric. Professional sports bettors typically target 3–8% ROI. Above 10% is exceptional and should be scrutinized for overfitting.

### Yield

Often used interchangeably with ROI. Specifically: profit per unit staked.

### Win Rate

Percentage of bets that won. Meaningful only in the context of the odds. A 45% win rate on `+150` underdogs is highly profitable; a 52% win rate on `-120` favorites is roughly break-even.

### Maximum Drawdown

The largest peak-to-trough decline in the simulated bankroll. A model may have positive ROI but a maximum drawdown of 40% — which would require extraordinary psychological fortitude (or an unrealistically large bankroll buffer) to survive in practice.

### Sharpe Ratio

```
Sharpe = (mean_return - risk_free_rate) / std_dev_of_returns
```

Measures return per unit of risk. Adapted from finance, it is useful for comparing models with similar ROI but different variance profiles.

### Closing Line Value (CLV)

The difference between the odds you (simulated) received and the closing line odds. Consistently positive CLV is a stronger validation signal than raw ROI — see [`market-efficiency.md`](../foundations/market-efficiency.md) for why.

## The Overfitting Problem

Backtesting creates a dangerous feedback loop: you test a model, observe poor results, tune the model or add features, retest, and repeat. Each iteration that uses the test data to guide modeling decisions is a form of overfitting to the historical sample.

Signs of an overfit backtest:

- ROI is above 10–15% with no obvious structural reason
- Model performs well in only one specific time window
- Adding more features or complexity consistently improves backtest results but performance degrades over the most recent data
- The model is sensitive to minor parameter changes

**Best practice**: hold out the most recent season of data entirely. Never touch it during model development. Only evaluate on it once, as a final validation before deployment.

## Sample Size Considerations

Sports seasons are short. An NFL season has 16–17 games per team. With 32 teams, you have roughly 256–272 games per season. At a bet frequency of one game per week, you might generate 200–300 bets per season.

Statistical significance guidelines:

| Sample size | What you can conclude |
|------------|----------------------|
| < 500 bets | Results are noise. Do not draw conclusions. |
| 500–1,000 bets | Preliminary signal. Directionally useful. |
| 1,000–2,000 bets | Meaningful signal with reasonable confidence. |
| 2,000+ bets | Statistically robust conclusions. |

For most sports, you need multiple seasons of backtesting data to produce statistically meaningful results. Be especially skeptical of models that show strong performance on only one or two seasons.

## Practical Checklist

Before trusting any backtest result:

- [ ] All features are computed using strictly pre-game data
- [ ] Historical odds reflect what was actually available, not closing or reconstructed prices
- [ ] Walk-forward validation was used (no in-sample testing)
- [ ] A held-out final test period exists and has not been touched during development
- [ ] Bet selection logic matches the intended production strategy
- [ ] Sample size exceeds 1,000 bets before drawing conclusions
- [ ] Maximum drawdown and variance are within acceptable ranges
- [ ] CLV is monitored alongside ROI
