# Quantile Regression

Quantile regression predicts a specific quantile of the outcome distribution rather than just the mean. In sports betting, this is particularly valuable for spread and totals markets, where predicting the full distribution of possible scores — not just the average — allows for more precise market pricing.

## Why the Mean Is Not Enough

Standard regression models predict the expected (mean) value of an outcome. For betting purposes, this is often insufficient:

- A totals line of 48.5 needs you to estimate `P(total > 48.5)`, not just the mean total
- A spread of -7 needs you to estimate `P(home_margin > 7)`, not just the average margin
- The distribution of outcomes may be asymmetric — large blowouts pull the mean higher than the median

Point spreads explain approximately 86% of the variance in NFL game outcomes. But explaining variance is not the same as accurately pricing the tails of the distribution. Quantile regression directly targets those tails.

## The Quantile Loss Function

Standard regression minimizes squared error, which targets the mean. Quantile regression minimizes the "pinball" or "check" loss, which targets a specific quantile `τ` (tau, between 0 and 1):

```
L_τ(y, ŷ) = τ × max(y - ŷ, 0) + (1 - τ) × max(ŷ - y, 0)
```

Where:
- `y` is the actual outcome
- `ŷ` is the predicted value
- `τ` is the target quantile

When `τ = 0.5`, this is the median absolute deviation loss (targets the median). When `τ = 0.75`, the model is optimized to predict the 75th percentile of the outcome distribution.

The asymmetric weighting is key: for `τ = 0.75`, under-predictions (actual > predicted) are penalized by weight `0.75` and over-predictions are penalized by weight `0.25`. This incentivizes the model to find a value that is exceeded by exactly 25% of outcomes — the 75th percentile.

## Application to Totals Markets

To estimate the probability that total points exceed a line `L`:

1. Train a quantile regression model with `τ` values spanning [0.1, 0.9] at fine intervals
2. For a specific game, predict the full spectrum of quantiles: `q_0.1, q_0.2, ..., q_0.9`
3. Find where the line `L` falls within this predicted quantile function
4. Interpolate to estimate `P(total > L)`

This produces a full predicted CDF for total points, allowing you to price any totals line — not just the specific line you trained on.

### Example

For an upcoming NBA game, your quantile model predicts:

| Quantile | Predicted total |
|---------|----------------|
| 10th | 196 |
| 25th | 208 |
| 50th | 218 |
| 75th | 228 |
| 90th | 240 |

The bookmaker sets a line of 222.5. Your model estimates `P(total > 222.5) ≈ 62%`. If the bookmaker prices the over at `-110` (52.4% implied probability), you have a 10-point edge — a strong value bet on the over.

## Application to Spread Markets

Same logic applies to point differentials:

1. Train quantile regression on historical home team margin of victory
2. For a specific game, predict the distribution of margins
3. Compare `P(home_margin > spread)` against the bookmaker's implied probability

If the spread is -3.5 and your distribution gives a 58% probability of the home team covering, but the line implies only 52.4%, you have a value bet.

## Quantile Regression Forests

Standard (linear) quantile regression assumes a linear relationship between features and the conditional quantile. Quantile Regression Forests (QRF) extend the approach non-parametrically:

1. Train a random forest normally
2. For predictions, instead of averaging leaf node values, keep the full distribution of training examples that fall into each leaf
3. Estimate any quantile from that distribution

QRF is particularly well-suited to sports betting because:
- It captures non-linear feature interactions (e.g., pace interacts with rest in ways that matter for totals)
- It produces the full conditional distribution, not just a specific quantile
- No assumption about the shape of the outcome distribution

The cost is less interpretability and higher computational requirements than linear quantile regression.

## Gradient Boosting with Quantile Loss

XGBoost and LightGBM both support quantile loss as a training objective. This gives you the flexibility of tree-based models combined with targeted quantile prediction. Configure by setting the objective to `quantile` and specifying `alpha = τ`.

## Feature Inputs for Totals Models

Totals models need features specifically predictive of scoring volume, not just who wins:

- **Pace** (possessions per game, or equivalent sport-specific metric)
- **Offensive rating** (points per possession, or goals per game)
- **Defensive rating** (points allowed per possession, or goals conceded per game)
- **Combined team averages**: sum of both teams' offensive and defensive metrics
- **Environmental factors**: weather (outdoor sports), altitude, dome vs. outdoor
- **Rest and travel**: tired teams may play at a different pace
- **Game context**: teams with playoff spots locked up may not play full intensity

## Crossing Quantiles: A Practical Issue

A known challenge with training separate models for each quantile: predictions from different quantile models can "cross" — the 75th percentile prediction may be lower than the 50th percentile prediction for some observations. This violates the basic requirement that quantiles are monotonically ordered.

Solutions:
- **Joint quantile regression**: train all quantiles simultaneously with a crossing penalty in the loss function
- **Isotonic post-processing**: after prediction, apply isotonic regression to enforce monotonicity
- **Use QRF instead**: forests produce non-crossing quantiles by construction

## Comparison with Poisson for Goal Totals

In soccer, Poisson models (see [`models/poisson.md`](poisson.md)) also price totals markets by summing the joint probability distribution. Quantile regression offers a complementary approach:

- **Poisson**: mechanistic model based on goal-scoring theory; interpretable; works well when the data volume is small
- **Quantile regression**: data-driven; captures non-Poisson patterns (overdispersion, score effects); requires more historical data to train reliably

In practice, both approaches are worth implementing and comparing against each other and against the market.
