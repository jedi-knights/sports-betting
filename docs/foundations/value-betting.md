# Value Betting

Value betting is the foundation of every profitable sports betting approach. Understanding it is a prerequisite for everything else in this repository.

## The Core Idea

A bookmaker converts their estimate of each outcome's probability into odds, then adds a margin (the vig) on top. When you place a bet, you are implicitly disagreeing with the bookmaker's probability estimate. A value bet is a bet where your estimate of the true probability is higher than the probability implied by the offered odds.

If you can consistently identify these situations — and your probability estimates are correct — you will be profitable in the long run regardless of short-term variance.

## Implied Probability

Every set of odds encodes a probability. To extract it:

**Decimal odds:** `implied_probability = 1 / decimal_odds`

Example: odds of 2.50 imply a probability of `1 / 2.50 = 0.40` (40%).

**American odds:**
- Negative (favorite): `implied_probability = |odds| / (|odds| + 100)`
- Positive (underdog): `implied_probability = 100 / (odds + 100)`

Example: `-150` implies `150 / 250 = 0.60` (60%). `+130` implies `100 / 230 ≈ 0.435` (43.5%).

These raw implied probabilities include the bookmaker's margin. To get a cleaner estimate of what the market truly believes, you need to remove the vig first (see the vig removal section below).

## The Expected Value Formula

Expected value (EV) is the theoretical average profit per bet placed over a large number of repetitions.

```
EV = (p_win × profit_if_win) - (p_lose × stake)
```

Where:
- `p_win` = your estimated probability of winning
- `profit_if_win` = net profit (stake × (decimal_odds - 1))
- `p_lose` = 1 - p_win
- `stake` = amount wagered

A simpler expression using decimal odds and your estimated probability `p`:

```
EV per unit = (p × decimal_odds) - 1
```

If this number is positive, the bet has positive expected value. If negative, you are expected to lose money.

### Example

A team is priced at decimal odds of `2.10` (implied probability: 47.6%). Your model estimates their true win probability at 55%.

```
EV per unit = (0.55 × 2.10) - 1 = 1.155 - 1 = +0.155
```

For every $1 wagered on this bet, you expect to gain $0.155 in the long run. That is a 15.5% edge — a large edge by any professional standard.

## Removing the Vig

Bookmakers price both sides of a market so that the implied probabilities sum to more than 100%. The excess is their margin. For a two-outcome market (e.g., Team A wins vs. Team B wins):

```
vig = (implied_p_A + implied_p_B) - 1
```

To get no-vig probabilities:

```
no_vig_p_A = implied_p_A / (implied_p_A + implied_p_B)
no_vig_p_B = implied_p_B / (implied_p_A + implied_p_B)
```

### Example

Team A: `-130` → implied probability = `130/230 ≈ 0.565`
Team B: `+110` → implied probability = `100/210 ≈ 0.476`

Sum = 1.041. Overround = 4.1%.

No-vig probabilities:
- Team A: `0.565 / 1.041 ≈ 0.543` (54.3%)
- Team B: `0.476 / 1.041 ≈ 0.457` (45.7%)

Sum = 100%. These are cleaner estimates of what the market truly believes.

## What Creates Value

Value arises from informational or analytical advantages:

1. **Faster information** — knowing about an injury, weather change, or lineup decision before it is reflected in the odds.
2. **Better models** — estimating probabilities more accurately than the market through superior data or methodology.
3. **Market inefficiencies** — certain bet types (props, futures, smaller leagues) have less sharp action and therefore less efficient prices.
4. **Public bias** — recreational bettors systematically overbet popular teams, home teams, and favorites. Lines in heavily bet markets can be shaded to extract more from recreational bettors.

## Why Edge Disappears

Markets become more efficient as information is incorporated. Most large markets (NFL moneylines, NBA point totals) are highly efficient by game time — the closing line represents a near-optimal probability estimate. Finding consistent edges there is very difficult.

Smaller markets (lower-division soccer, college sports, player props) are less efficiently priced and offer more opportunity.

## The Relationship Between Edge and Long-Run Profit

Even a small consistent edge compounds significantly over thousands of bets. A 2% EV edge on $100 bets placed 1,000 times yields an expected profit of $2,000. The key word is "expected" — variance means actual results will fluctuate around this expectation, especially over shorter sample sizes.

This is why bet sizing and bankroll management (see [`bankroll-management.md`](../strategy/bankroll-management.md)) are as important as finding edge in the first place.

## The Role of Calibration

Finding value requires estimating probabilities accurately. A model that is systematically miscalibrated — for example, one that says "70% probability" when the true rate is only 60% — will identify false value and lead to long-run losses. This is why calibration is arguably the most important property of a betting model. See [`calibration.md`](../modeling/calibration.md).

## Key Takeaways

- A value bet is not a guaranteed winner — it is a bet with positive expected value.
- Short-term losses are inevitable even with genuine edge; the long run is what matters.
- The bookmaker's odds are your adversary's estimate. Your model needs to be better, not just different.
- Even a small, reliable edge compounds to significant profit over large bet volumes.
