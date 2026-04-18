# Bankroll Management

Finding value bets is necessary but not sufficient for long-run profitability. How you size those bets determines whether a genuine edge translates into profit or ruin. This document covers the mathematics of bet sizing, the Kelly Criterion, its practical variants, and the psychological realities of managing a betting bankroll.

## Why Bet Sizing Matters

Consider two bettors, both with a 5% edge on every bet. Bettor A bets 1% of their bankroll per bet. Bettor B bets 50% of their bankroll per bet.

Over 100 bets, Bettor A grows their bankroll steadily. Bettor B will almost certainly be ruined — even with genuine positive EV — because the variance from overbetting exceeds the edge. This is not hypothetical: the mathematics of geometric growth means that overbetting with any amount above the Kelly fraction leads to long-run bankruptcy.

## The Kelly Criterion

The Kelly Criterion, developed by John L. Kelly Jr. in 1956, is the mathematically optimal bet-sizing formula for maximizing the long-run growth rate of a bankroll.

### Formula (Binary Outcome)

```
f* = (bp - q) / b
```

Where:
- `f*` = fraction of bankroll to wager
- `b` = net odds received (profit per unit staked; decimal odds minus 1)
- `p` = estimated probability of winning
- `q` = estimated probability of losing = 1 - p

### Example

Your model estimates a 55% probability of winning. The available odds are `-110` (decimal: 1.909), so `b = 0.909`.

```
f* = (0.909 × 0.55 - 0.45) / 0.909
f* = (0.500 - 0.45) / 0.909
f* = 0.050 / 0.909
f* ≈ 0.055 (5.5% of bankroll)
```

At a 55% win rate on `-110` odds, you should bet 5.5% of your bankroll.

### Alternative Formulation (Using Probabilities Directly)

If you express your edge in terms of your probability `p` vs. the market's implied probability `q_market`:

```
f* = p - q_market / b
```

Or more directly:

```
f* = (p × decimal_odds - 1) / (decimal_odds - 1)
```

### What Kelly Maximizes

Kelly maximizes the expected logarithm of wealth, which is equivalent to maximizing the long-run compound growth rate. This is the right objective for repeated betting over a long horizon.

Kelly does not maximize expected profit on any single bet — it sacrifices some upside to protect against ruin.

## Why Full Kelly Is Dangerous in Practice

The Kelly formula assumes your probability estimates are perfectly accurate. In practice, they never are. If your model says 60% but the true probability is 52%, full Kelly will overbet and erode the bankroll.

Additionally, full Kelly produces extreme variance. A Kelly bettor should expect to see their bankroll cut in half with some regularity — this is mathematically expected behavior, not a sign something is wrong. Most bettors (and most organizations) cannot sustain this psychologically or financially.

### The Overbetting Trap

Kelly defines the optimal fraction, but it also defines a boundary: betting more than the full Kelly fraction produces lower long-run growth than betting the Kelly fraction. Betting double Kelly eventually leads to ruin with probability 1. Betting more than Kelly is strictly worse in expectation than betting less than Kelly.

## Fractional Kelly

The standard practical approach is to bet a fixed fraction of the Kelly-recommended amount:

- **Half Kelly (½ Kelly)**: bet 50% of `f*`
- **Quarter Kelly (¼ Kelly)**: bet 25% of `f*`

### Trade-offs

| Strategy | Growth rate | Variance | Ruin risk |
|----------|------------|----------|-----------|
| Full Kelly | Maximum | Very high | Low (but real) |
| Half Kelly | ~75% of full Kelly | Much lower | Very low |
| Quarter Kelly | ~44% of full Kelly | Low | Negligible |

Half Kelly is the most common choice among professional bettors. It captures about 75% of the theoretically optimal growth rate at roughly 25% of the variance, and it provides a buffer against model miscalibration.

## Fixed-Unit (Flat) Staking

An alternative to Kelly-based sizing: bet a fixed number of units (e.g., 1 unit = 1–2% of bankroll) on every qualifying bet, regardless of the estimated edge magnitude.

**Pros:**
- Simple to implement
- Prevents overbetting on bets where your model is miscalibrated
- Easier to track performance across different bettor sizes (just count units)

**Cons:**
- Does not scale bet size with edge magnitude — a 15% edge gets the same bet as a 2% edge
- Suboptimal growth rate compared to Kelly
- Requires periodic bankroll resets to maintain unit size as bankroll grows/shrinks

Fixed-unit staking is often recommended for bettors who are new to quantitative methods because it prevents the compounding mistakes that arise from overconfident probability estimates.

## The Bankroll Structure

### Starting Bankroll

Your starting bankroll should be money you can afford to lose entirely. Even with a genuine edge, variance ensures short-term losses are expected. A bankroll that is "can't lose" money will cause emotional decision-making that degrades performance.

Minimum practical starting bankroll for meaningful volume: enough to place 200–500 units without approaching ruin.

### Tracking and Rebasing

As your bankroll grows, your unit size should grow proportionally (if using Kelly or percentage-based staking). As it shrinks, your unit size must shrink — failure to scale down is one of the most common causes of bankroll ruin in practice.

Establish rebase checkpoints: at every 10% bankroll increase or decrease, recalculate your unit size.

### Separation of Funds

Keep betting bankroll strictly separate from living expenses. Commingling funds leads to forced bets during drawdowns (chasing losses) and premature withdrawals during upswings.

## Ruin Probability

Even with positive EV and correct Kelly sizing, ruin (bankroll reaching zero) is possible. The probability depends on edge, variance, and the fraction of Kelly wagered.

For full Kelly betting with a small edge:
- Probability of halving your bankroll before doubling it: approximately 33%
- Probability of bankroll dropping to 10% of starting value: approximately 10%

For ½ Kelly:
- Probability of halving before doubling: drops significantly
- Permanent ruin becomes extremely unlikely

This is why many professional operations treat drawdown limits as hard stops. For example: if the bankroll drops 30% from its peak, stop betting and revalidate the model before continuing.

## Drawdown Expectations

Understanding expected drawdowns helps distinguish normal variance from a broken model.

A general rule of thumb: even a profitable strategy with 5% edge on standard lines will regularly experience 10–20% drawdowns over the course of a season. A 30% drawdown is unusual but not impossible. A 50%+ drawdown should trigger a model review.

Track drawdown alongside ROI in every backtest. A strategy with 8% ROI and 40% maximum drawdown may be inferior to a strategy with 5% ROI and 12% maximum drawdown, depending on your risk tolerance and starting bankroll.

## Multi-Sport and Multi-Market Portfolios

When betting across multiple sports or market types simultaneously, the Kelly Criterion still applies but must account for correlation between bets.

- Bets on the same game (e.g., spread + total) are correlated — sizing them independently overstates the total Kelly fraction
- Games in the same sport on the same day may be correlated through weather, travel, referee assignment, etc.
- The full portfolio-Kelly calculation becomes complex; a conservative practical approach is to reduce individual bet sizes when multiple bets share common risk factors

## Key Takeaways

- The Kelly Criterion is the theoretically optimal bet-sizing formula, but requires accurate probability estimates to use safely.
- Overbetting (above full Kelly) reduces long-run growth and eventually causes ruin — more dangerous than underbetting.
- Half Kelly is the standard starting point for practitioners: ~75% of optimal growth at much lower variance.
- Fixed-unit staking is simpler and safer for new practitioners while model calibration is still being validated.
- Drawdown management is as important as finding edge — a model that causes 50% drawdowns is not deployable regardless of long-run ROI.
