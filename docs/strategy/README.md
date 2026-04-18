# Strategy

The documents in this section cover the operational side of sports betting: what to do once your model produces a probability estimate. Finding a positive-EV opportunity is only half the problem — executing it correctly, sizing it appropriately, and maintaining the accounts needed to do so over the long run are equally important.

These documents assume familiarity with [Value Betting](../foundations/value-betting.md) (what positive EV means) and [Calibration](../modeling/calibration.md) (why your probability estimates need to be trustworthy before you apply any of the techniques here).

## Documents

### [Bankroll Management](bankroll-management.md)

The Kelly Criterion is the mathematically optimal bet-sizing formula: it maximizes the long-run growth rate of your bankroll given a known edge and known odds. This document derives the formula, explains what it maximizes, and explains why the theoretically optimal answer (full Kelly) is dangerous in practice.

Key topics:
- Kelly Criterion derivation and examples at varying edge levels
- Why overbetting above the Kelly fraction leads to long-run ruin even with positive EV
- Fractional Kelly (½ Kelly, ¼ Kelly): the standard practitioner approach — ~75% of optimal growth at much lower variance
- Fixed-unit (flat) staking: simpler, safer, recommended while model calibration is still being validated
- Expected drawdown ranges and what distinguishes normal variance from a broken model
- Multi-sport portfolio considerations: when bets are correlated, independent Kelly sizing overstates your total exposure

**Read this before placing any real money.** Correct bet sizing is as important as finding edge — a bettor with genuine edge who bets too large will still go bankrupt.

---

### [Line Shopping and Account Management](line-shopping-and-account-management.md)

Getting the best available price on every bet is one of the simplest ways to improve long-run returns — and maintaining the accounts needed to do it is a non-trivial operational challenge.

Key topics:
- Why the difference between -110 and -105 matters across 1,000 bets
- Sharp books (Pinnacle, Circa) vs. soft books (DraftKings, FanDuel) vs. exchanges (Betfair): what each is good for and what to expect from each
- Getting limited: how bookmakers identify profitable bettors and what to do about it
- Recommended multi-book setup for a serious operation
- Timing bets: early lines vs. late lines, and when each is preferable
- Record keeping for account management (separate from bet performance tracking)
- Withdrawal strategy and fund distribution across accounts

---

### [Prop Betting](prop-betting.md)

Player proposition markets — individual player performance bets (rushing yards, strikeouts, rebounds) — have higher bookmaker margins than game lines but typically less sharp monitoring, making them one of the more accessible sources of model-based edge.

Key topics:
- Why props offer more edge than game lines (higher margin, less sharp action, more cross-book discrepancy)
- Major prop categories by sport: NFL passing/rushing, NBA points/rebounds/assists, MLB strikeouts, NHL shots
- Building a player props model: baseline projection → matchup adjustment → game context → distribution modeling
- Modeling the full distribution (Poisson or normal) to price any line, not just the one set by the book
- Correlated props and same-game parlays: why SGPs are almost always negative EV
- Data sources for player-level statistics by sport
- Common pitfalls: small samples, injury/role changes, stacking model errors

---

### [Arbitrage and Middles](arbitrage-and-middles.md)

Two strategies that exploit bookmaker price discrepancies rather than requiring a model-based edge: arbitrage (guaranteed profit across all outcomes) and middles (positioning to win both sides of a moved line).

Key topics:
- Arbitrage: the math for calculating whether a cross-book arb exists and how to size each leg
- Real-world limitations: speed, account bans, void risk, and why effective margins are much smaller than headline numbers
- Middles: how NFL key numbers (3, 7) create the most valuable middle opportunities
- Middle EV calculation: the breakeven hit rate and why the 3-7 window in NFL exceeds it
- Matched betting: using bookmaker sign-up promotions to extract free bet value with minimal risk
- Arbitrage vs. value betting: why arbing has a lower ceiling despite no model requirement

---

### [Hedging](hedging.md)

Placing a bet on the opposite side of an existing open position to reduce or eliminate exposure. Mathematically justified in exactly two situations; emotionally tempting in many more.

Key topics:
- The two legitimate reasons to hedge: your model's probability has changed significantly, or the variance exceeds what your current bankroll can sustain under Kelly sizing
- The EV cost of hedging: a locked-in profit is always less than the expected value of the unhedged position (assuming positive EV)
- How to calculate the stake that locks in a specific guaranteed profit
- Partial hedges: reducing exposure without eliminating it, useful when the position exceeds Kelly but retains upside value
- Practical scenarios: futures bets that hit mid-season, in-game live betting hedges
- The psychological trap: why most hedges are placed for emotional reasons (loss aversion, proximity to the outcome) and how to identify and resist them

---

### [Tournament and Playoff Modeling](tournament-and-playoff-modeling.md)

Playoff and tournament betting has structurally different characteristics from regular-season betting: smaller samples, changed home-field dynamics, no load management, and path-dependent bracket outcomes.

Key topics:
- Why regular-season models don't transfer directly to playoffs (sample collapse, effort selection, coaching adjustment risk)
- Home-field advantage in NFL, NBA, MLB, and NHL playoffs vs. regular season values
- Series modeling: converting per-game win probability to series win probability using the binomial formula
- Home-court-adjusted series simulation using Monte Carlo when location varies by game
- Tournament bracket simulation: assigning round-by-round probabilities and comparing against futures odds
- Path dependency: why a team on the "easy side" of a bracket has a different championship probability than the same team on the "hard side," even at equal per-game strength
- Practical adjustments: upweight efficiency metrics over raw results, widen uncertainty intervals, account for matchup-specific factors

## Recommended Reading Order

If you are new to the strategy side, read in this order:

1. **Bankroll Management** — before any other strategy work
2. **Line Shopping and Account Management** — operational foundation for everything else
3. **Prop Betting** — if you want to start with a higher-edge, lower-competition market
4. **Hedging** — when you have open futures positions
5. **Arbitrage and Middles** — supplementary to a model-based approach, not a replacement
6. **Tournament and Playoff Modeling** — when the postseason begins

## How This Section Relates to the Rest

- **[Foundations](../foundations/README.md)** explains the concepts (EV, market efficiency, variance) that this section applies
- **[Modeling](../modeling/README.md)** produces the probability estimates that bankroll management and line shopping act on
- **[Sport-Specific](../sport-specific/README.md)** guides specify how strategy considerations vary by sport (e.g., NHL account management around goaltender confirmation; NFL timing around injury report windows)
