# Variance and Sample Size

One of the most common mistakes in sports betting — especially for newcomers — is drawing conclusions from too small a sample. A bettor can go 60-40 over 100 bets and genuinely not know whether they have a real edge or got lucky. This document explains the mathematics of variance in betting, how to calculate the sample sizes needed for meaningful conclusions, and how to interpret short-run results without being misled by them.

## Why Sports Betting Is High-Variance

Each individual bet is a binary event: win or lose. Even with a genuine 5% edge, a single bet has a roughly 47–52% chance of losing (depending on the odds). That is a coin flip with a slight tilt — and short sequences of coin flips are dominated by randomness.

Unlike a casino game where you can run millions of hands overnight, a sports bettor might place 500–1,000 bets in an entire season. That sample size is small enough that variance routinely swamps true edge over any reasonable timeframe.

## The Binomial Distribution

A series of independent bets with the same win probability follows a binomial distribution. For `n` bets with win probability `p`:

- **Expected wins**: `μ = n × p`
- **Standard deviation**: `σ = √(n × p × (1 - p))`

### Example

You have a true 55% win rate on even-money bets. Over 100 bets:

```
μ = 100 × 0.55 = 55 wins
σ = √(100 × 0.55 × 0.45) = √24.75 ≈ 4.97
```

One standard deviation spans roughly 50–60 wins. Two standard deviations spans 45–65 wins. You can go 45-55 (a losing record) purely from variance even when your true edge is 55%. This is not unusual — it is statistically expected to happen roughly 5% of the time.

## Standard Deviation of Returns

For bets placed at varying odds, the binomial formula understates the true variance because different odds produce different profit/loss magnitudes. A more complete measure uses the standard deviation of individual bet returns.

For a single bet with win probability `p` at decimal odds `d`:

```
E[return] = p × (d - 1) - (1 - p) = p × d - 1
Var[return] = p × (d - 1)² + (1 - p) × 1² - (E[return])²
```

For a portfolio of `n` bets with consistent sizing:

```
σ_portfolio = σ_single × √n
```

This is why even a profitable strategy will show large bankroll swings over short samples — the per-bet variance is high relative to the per-bet expected value.

## How Many Bets Before Conclusions?

The rule of thumb in the industry: **1,000 bets minimum before drawing meaningful conclusions**. Here is why.

To detect a 5% edge (ROI = 5%) with 90% confidence at standard flat stakes on `-110` lines:

```
Required n ≈ (z × σ / target_ROI)²
```

Where `z = 1.645` (90% confidence), `σ ≈ 1.0` (approximate standard deviation of return per unit), and `target_ROI = 0.05`:

```
n ≈ (1.645 × 1.0 / 0.05)² = (32.9)² ≈ 1,083
```

For 95% confidence: approximately 1,500 bets. For a 3% edge: approximately 3,000 bets.

### Practical Implications by Sport

| Sport | Bets per season (single bettor) | Seasons to reach 1,000 bets |
|-------|--------------------------------|----------------------------|
| NFL | 100–250 | 4–10 seasons |
| NBA | 300–600 | 2–3 seasons |
| MLB | 400–800 | 1–2 seasons |
| Soccer (top league) | 200–400 | 2–5 seasons |
| Multi-sport | 500–1,500 | 1–2 seasons |

This is the uncomfortable truth: for a single-sport bettor at normal bet frequencies, statistical certainty requires years of data. The professional response is not to abandon caution but to:
1. Bet more markets within a sport (totals + spreads + moneylines)
2. Track closing line value as a leading indicator (see below)
3. Treat early results as a prior to be updated, not a conclusion

## The Luck vs. Skill Boundary

A useful framework: at any given win rate and sample size, calculate the probability that the observed record could occur by chance assuming no edge.

For a 60-40 record on even-money bets (no edge → true win rate = 50%):

```
P(≥ 60 wins in 100 bets | p = 0.50) = binomial_cdf(60, 100, 0.5) ≈ 2.8%
```

A 2.8% p-value means this record would occur by chance about once in 36 such 100-bet sequences. Unusual, but not convincing evidence of edge. The same 60% win rate over 500 bets has a p-value below 0.0001 — that is significant.

### Z-Score for Betting Records

A quick way to test whether a record is statistically significant assuming a break-even model (implied win rate from the odds):

```
z = (actual_wins - expected_wins) / σ
```

Where `expected_wins = n × break_even_rate` and `σ = √(n × p × (1-p))`.

- `|z| > 1.645`: significant at 90% confidence
- `|z| > 1.96`: significant at 95% confidence
- `|z| > 2.576`: significant at 99% confidence

## Closing Line Value as a Leading Indicator

Because large bet samples take years to accumulate, professional bettors use closing line value (CLV) as a proxy for edge quality rather than waiting for win/loss statistics to converge. See [`market-efficiency.md`](market-efficiency.md).

The advantage of CLV: every single bet generates a CLV data point immediately. Over 200 bets, consistent positive CLV provides meaningful evidence of edge well before the win/loss record does.

## Downswings: Expected and Unexpected

### What a Normal Downswing Looks Like

Even with a 55% win rate on even-money bets, downswings of significant length are normal:

| Streak | Probability of occurrence |
|--------|--------------------------|
| 5 consecutive losses | ~1.5% per sequence of 5 bets (~once per 66 bets) |
| 10 consecutive losses | ~0.2% per sequence of 10 bets (~once per 500 bets) |
| Losing record over 50 bets | ~8% |
| Losing record over 100 bets | ~5% |

Over a full 500-bet season, a bettor with genuine 55% edge should expect at least one run of 8–10 consecutive losses. This is variance, not signal. The correct response is to maintain the strategy, not abandon it.

### When a Downswing Is a Warning Sign

A downswing becomes worth investigating when:
- CLV is consistently negative (you are getting worse prices than the closing line)
- The downswing is statistically extreme (z-score below -2.5 or worse)
- The losing markets are ones where your model's assumptions may have broken down (rule change, key personnel change, market evolution)

## Confidence Intervals for ROI

Rather than reporting a single ROI number, report a confidence interval:

```
ROI_CI = ROI ± z × (σ / √n)
```

For 500 bets with observed ROI = 6% and σ ≈ 1.0:

```
95% CI = 6% ± 1.96 × (1.0 / √500) = 6% ± 8.8% = [-2.8%, 14.8%]
```

The true ROI could plausibly be negative at this sample size. This is the honest way to report early results.

## Key Takeaways

- 100 bets proves almost nothing. 1,000 bets is the minimum for directional signal. 2,000+ bets begins to approach statistical reliability.
- Downswings of 10+ bets are mathematically expected for any reasonable edge. Do not abandon a model during normal variance.
- Track CLV alongside win/loss to get earlier evidence of whether your model has genuine edge.
- Always report ROI with a confidence interval, not as a point estimate.
- The professional response to uncertainty is not to make faster conclusions — it is to operate with appropriate position sizing while the sample accumulates.
