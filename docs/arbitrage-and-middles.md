# Arbitrage and Middles

Arbitrage and middles are strategies that exploit discrepancies between bookmakers rather than requiring a probabilistic edge. In pure arbitrage, you lock in a guaranteed profit regardless of outcome. In a middle, you position yourself to profit from both sides of a line movement. Neither requires your model to be correct about the outcome — only about where prices differ.

## Arbitrage (Sure Bets)

### What It Is

An arbitrage opportunity exists when the odds at different bookmakers allow you to bet all sides of a market and guarantee a profit regardless of which outcome occurs.

This happens because different bookmakers set their lines independently and sometimes end up on opposite sides of fair value for the same event.

### How to Calculate

For a two-outcome market (Team A vs. Team B), an arb exists when:

```
(1 / odds_A_at_book_1) + (1 / odds_B_at_book_2) < 1
```

If this sum is less than 1, the combined implied probabilities are below 100% — meaning the vig is negative across the combination and profit is guaranteed.

### Example

- Book 1 offers Team A at `+120` (decimal: 2.20) → implied probability: `1/2.20 = 45.5%`
- Book 2 offers Team B at `+115` (decimal: 2.15) → implied probability: `1/2.15 = 46.5%`
- Combined: `45.5% + 46.5% = 92%` → arbitrage margin = `8%`

Since the sum is below 100%, an arb exists. To find optimal stakes:

```
stake_A = (arb_margin × total_stake) / odds_A
stake_B = (arb_margin × total_stake) / odds_B
```

More practically: stake proportional to `1/odds` on each side, sized so both outcomes return the same total.

For a $1,000 total stake:

```
stake_A = 1000 × (1/2.20) / (1/2.20 + 1/2.15) = $494
stake_B = 1000 × (1/2.15) / (1/2.20 + 1/2.15) = $506

If A wins: $494 × 2.20 = $1,087 (profit: $87)
If B wins: $506 × 2.15 = $1,088 (profit: $88)
```

Guaranteed ~8.7% return on $1,000 wagered, regardless of outcome.

### Real-World Limitations

**Account limits and bans**: bookmakers that consistently receive arb bets quickly identify and limit or ban those accounts. Since arbs require placing bets at multiple books simultaneously, you are visible to every book involved. Soft books (DraftKings, FanDuel) are particularly aggressive about limiting arbers.

**Speed**: arb windows often close within minutes of opening. Prices move continuously, and the arb may disappear before you can place both sides.

**Stake matching**: you need sufficient balance at both books simultaneously. Large arbs require large funds spread across multiple accounts.

**Void risk**: if one leg of an arb is voided (e.g., a game postponed, a player ruled ineligible) while the other stands, you may be left with a single unhedged position.

**Effective profit margin**: after accounting for the above friction, most accessible arbs yield 1–3%, not the headline percentages. The capital required to generate meaningful income from arbing alone is substantial.

### Where Arbs Are Found

- Moneyline discrepancies between a sharp book (Pinnacle) and a slow-adjusting soft book
- Futures markets where different books have different assessments of the same team
- Live betting, where fast-moving odds occasionally create brief cross-book arbs
- Bonus-fueled arbs (using sign-up offers to guarantee a profit) — a specific strategy called "matched betting"

---

## Middles

### What It Is

A middle occurs when you bet both sides of a market at different line values, creating a range of outcomes where both bets win simultaneously.

Unlike arbitrage, a middle does not guarantee profit — you can still lose on both sides. But if the outcome "falls in the middle," you win both bets. The risk profile is: small guaranteed loss vs. occasional large windfall.

### How It Works

Suppose the spread on Team A opens at `-3`. You bet Team A `-3` (they must win by 4+ to cover). The line then moves to `-6`. You now bet Team B `+6` (they can lose by up to 5 and still cover).

Your position:
- **Team A wins by 4 or 5**: both bets win (the middle hits)
- **Team A wins by 7+**: Team A `-3` wins, Team B `+6` loses → net roughly break even (depending on vig)
- **Team A wins by 1-2**: Team A `-3` loses, Team B `+6` wins → net roughly break even
- **Team A wins by exactly 3 or 6**: one bet wins, one pushes → small win
- **Team B wins**: Team B `+6` wins, Team A `-3` loses → net roughly break even

The "middle" (win margin of 4 or 5) produces a double winner. The expected value of this strategy depends on the probability of hitting the middle vs. the vig paid on each side.

### Middle EV Calculation

For a standard `-110` / `-110` market (paying $100 to win $91):

Cost of middling: you lose approximately $9–10 per side if the middle does not hit (paying vig twice).

Breakeven: if the middle hits with probability `p`:

```
p × (profit when middle hits) = (1 - p) × (vig cost when middle misses)
p × $191 = (1 - p) × $19
p ≈ 0.09 (9%)
```

If the margin of 4–5 occurs more than 9% of the time, the middle is +EV. For NFL games, a 2-point window around key numbers (e.g., 3 and 7 — the two most common margins of victory) occurs frequently enough that middles are sometimes valuable.

### Key Numbers and Middles

In NFL betting, certain victory margins are far more common than others:

- **3 points**: most common margin (~15% of games)
- **7 points**: second most common (~9% of games)
- **10 points**: third most common (~6% of games)

A middle that spans from +3 to +7 captures these two key numbers and hits in roughly 24% of games — well above the 9% breakeven. This is the most sought-after NFL middle.

### Where Middles Arise

1. **Opening line movement**: bet early at one number, bet the opposite side when the line has moved enough to create a window
2. **Cross-book discrepancies**: Book A is slow to move; Book B has already adjusted — you get different numbers at each book simultaneously
3. **Injury news**: a key injury moves the line 3+ points rapidly, potentially creating a middle window

### Operational Requirements

- Multiple bookmaker accounts with available balances
- Continuous line monitoring (manual or via odds aggregator tools)
- Fast execution — middle windows can be brief
- Tracking all open positions to avoid accidentally being uncovered on one side

---

## Matched Betting

A specific arbitrage variant that uses bookmaker sign-up bonuses and free bets to guarantee profit. Bookmakers offer new customers "bet $X, get $X free bet" promotions. By placing a qualifying bet at the bookmaker and laying the same outcome on a betting exchange (like Betfair), you hedge out the result and extract the free bet value with minimal risk.

This is technically legal and widely practiced. It is not scalable (each promotion can only be used once) and bookmakers often restrict or close accounts once they identify matched betting patterns.

---

## Arbitrage vs. Value Betting: Which to Pursue?

| | Arbitrage | Value Betting |
|---|---|---|
| Requires edge? | No | Yes |
| Scalable? | Limited (account bans) | Yes |
| Guaranteed profit? | Per-bet yes | Long-run only |
| Account longevity | Short | Longer |
| Capital requirement | High (funds across books) | Lower |
| Skill ceiling | Low | High |

For a bettor focused on model development, value betting is the higher-ceiling strategy. Arbitrage and middles are useful supplements, particularly during periods of model uncertainty, but they are not a sustainable primary strategy at scale due to bookmaker restrictions.
