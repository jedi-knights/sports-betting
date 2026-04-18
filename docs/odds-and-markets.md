# Odds and Markets

Understanding how odds are structured and what market types exist is the necessary foundation before any modeling work. This document covers how bookmakers express probability, how to convert between formats, the different bet types you will encounter, and how bookmaker margins work.

## Odds Formats

Three formats are in common use worldwide. They all encode the same information — the relationship between stake, profit, and implied probability — just expressed differently.

### American Odds (Moneyline Odds)

The standard format in the United States. All values are relative to a $100 bet.

- **Negative number** (e.g., `-150`): how much you must stake to win $100 profit. A `-150` bet requires a $150 stake to win $100 (total return: $250).
- **Positive number** (e.g., `+130`): how much profit a $100 stake yields. A `+130` bet on $100 returns $230 total ($130 profit).

To convert to implied probability:
- Negative: `|odds| / (|odds| + 100)`
- Positive: `100 / (odds + 100)`

### Decimal Odds

Standard in Europe, Australia, and most international markets. Represents the total return per unit staked, including the return of the original stake.

- `2.00` = even money (double your money)
- `1.50` = bet $1, get back $1.50 (profit of $0.50)
- `3.75` = bet $1, get back $3.75 (profit of $2.75)

To convert to implied probability: `1 / decimal_odds`

To convert from American odds to decimal:
- Negative: `(100 / |odds|) + 1`
- Positive: `(odds / 100) + 1`

### Fractional Odds

Traditional format in the United Kingdom. Written as `profit/stake` (e.g., `5/2`).

- `5/2` means: for every 2 units staked, profit is 5 units. Bet $2, profit $5, total return $7.
- `1/1` (evens): profit equals stake.
- `1/2`: stake is double the profit (odds-on favorite).

To convert to decimal: `(numerator/denominator) + 1`

### Quick Conversion Reference

| American | Decimal | Fractional | Implied Probability |
|----------|---------|------------|---------------------|
| -200 | 1.50 | 1/2 | 66.7% |
| -150 | 1.67 | 2/3 | 60.0% |
| -110 | 1.91 | 10/11 | 52.4% |
| +100 (even) | 2.00 | 1/1 | 50.0% |
| +120 | 2.20 | 6/5 | 45.5% |
| +150 | 2.50 | 3/2 | 40.0% |
| +200 | 3.00 | 2/1 | 33.3% |

---

## The Bookmaker Margin (Vig)

Bookmakers do not offer fair-odds markets. They price each side slightly worse than the true probability to guarantee profit regardless of outcome. This built-in margin is called the vig, juice, overround, or margin.

### How the Vig Works

In a two-outcome market (Team A vs. Team B), a fair market would have implied probabilities sum to exactly 100%. A typical bookmaker market might look like this:

- Team A: `-110` → implied probability = 52.4%
- Team B: `-110` → implied probability = 52.4%
- **Total: 104.8%**

The extra 4.8% is the overround — the bookmaker's guaranteed margin. No matter which team wins, the bookmaker profits from the combined excess.

### Standard Vig

In American football and basketball markets, `-110` on both sides of a spread or total is the standard. To break even at `-110` odds, you must win 52.38% of your bets. This "break-even rate" is a critical number — any model that performs below it on standard lines loses money.

Break-even rate at any odds: `|odds| / (|odds| + 100)` for favorites, `100 / (odds + 100)` for underdogs.

### Market-Specific Margins

- **Spread/totals markets**: typically 4–5% overround
- **Moneyline markets**: varies with the competitive balance; can be 5–10% on uneven matchups
- **Player props**: often 8–15% — much higher margin, harder to find value
- **Futures**: can exceed 25–30% overround across all outcomes

---

## Market Types

### Moneyline

A straight bet on which team or player wins the game. No point spread involved.

- Most straightforward bet type
- Requires larger stakes on heavy favorites to produce meaningful profit
- Common in baseball, hockey, soccer

### Point Spread

The bookmaker sets a handicap (the spread) on the favored team. To win a spread bet on the favorite, they must win by more than the spread margin. The underdog can lose by up to the spread amount and still cover.

Example: Team A -7.5 means Team A must win by 8+ points.

- Dominant in American football and basketball
- Standard vig is typically `-110` on both sides
- Spread markets are usually the most liquid and efficiently priced

### Totals (Over/Under)

A bet on whether the combined score of both teams will exceed (over) or fall short of (under) a bookmaker-set line.

- Depends on pace, defense, weather conditions, and scoring environment
- Quantile regression is particularly effective here (see [`models/quantile-regression.md`](models/quantile-regression.md))

### Props (Proposition Bets)

Bets on specific events within a game unrelated to the final score: individual player stats, first team to score, number of corners in a soccer match, etc.

- Higher bookmaker margins than game markets
- Less sharp action, so more potential for model-based edge
- Data requirements are more granular (player-level stats, tracking data)

### Futures

Long-term bets on outcomes like which team wins the championship, who wins MVP, etc.

- Very high margins (bookmakers often hold 25–30%)
- Capital is tied up for the full season
- Require predicting probability distributions across many outcomes simultaneously

### Parlays

Combining multiple bets into one. All legs must win for the parlay to pay. Payout is multiplicative.

Two-leg parlay at even odds: pays 3:1 (true fair payout: 4:1). Bookmakers keep approximately 25% of the theoretical fair value on standard parlays.

Same-game parlays (multiple bets from within one game) are even more heavily margined due to outcome correlations that bookmakers exploit.

### Live (In-Game) Betting

Bets placed during a game with continuously updated odds. Speed of model updates is critical — stale probabilities become worthless within seconds of a score, turnover, or injury.

---

## Line Shopping

No bettor should accept the first odds they see. Different bookmakers price the same event differently, and finding the best available price (line shopping) is one of the simplest ways to improve long-run returns.

A difference of `-110` vs. `-105` on the same bet reduces your break-even rate from 52.38% to 51.22% — a meaningful edge improvement without any modeling work.

In practice:
- Use multiple accounts across multiple bookmakers
- Record the odds you received vs. the closing line (see [`market-efficiency.md`](market-efficiency.md))
- Soft books (DraftKings, FanDuel) may offer better numbers on certain markets than sharp books

---

## Key Numbers in Spread Betting

Certain margin values appear more frequently than others in NFL and NBA outcomes due to how scoring works. In the NFL, the most common margins of victory are 3, 7, 10, and 6. A spread bet at `-3` is worth more than one at `-3.5` because a 3-point margin pushes (ties) rather than loses.

Understanding key numbers helps assess the true value of a given spread line vs. the fair-odds spread.
