# Foundations

The documents in this section cover the concepts you need to understand before building any model or placing any bet. They don't assume prior knowledge of statistics or sports betting — start here if you are new to the field.

## Reading Order

Work through these in order. Each document builds on the previous one.

1. **[Odds and Markets](odds-and-markets.md)** — Start here. Explains how odds work in all three formats (American, decimal, fractional), how to convert between them, what the bookmaker's margin is and how it's calculated, and the full range of bet types you will encounter (moneylines, spreads, totals, props, futures, parlays). Nothing else in this repository makes sense without this foundation.

2. **[Value Betting](value-betting.md)** — The central idea behind all model-based betting. Defines expected value (EV), explains how to calculate it from your probability estimate and the offered odds, shows how to remove the bookmaker's margin to get a clean probability estimate, and explains why a value bet is not a guaranteed winner — it is a bet where your estimated probability exceeds the market's. Everything in the modeling and strategy sections exists to identify and exploit value bets.

3. **[Market Efficiency](market-efficiency.md)** — Explains how and why bookmaker lines become accurate over time, the role of sharp bettors in that process, and why closing line value (CLV) — the difference between the odds you took and the odds at game time — is a better measure of model quality than win/loss record over short samples. Covers sharp vs. square action, steam moves, and which markets are most vs. least efficiently priced.

4. **[Variance and Sample Size](variance-and-sample-size.md)** — One of the most practically important documents in the repository. Shows mathematically why you need at minimum 1,000 bets before drawing conclusions about your model's edge, what a normal downswing looks like for a genuinely profitable strategy, how to calculate whether a record is statistically significant, and why CLV data accumulates evidence of edge much faster than win/loss data.

5. **[Psychology and Discipline](psychology-and-discipline.md)** — The mathematical framework only produces results if you execute it consistently. Documents the specific cognitive biases (recency bias, gambler's fallacy, loss aversion, confirmation bias, anchoring) that cause bettors to abandon profitable strategies at the worst possible moments, and the structural practices — pre-commitment, bet-execution separation, record keeping, scheduled reviews — that counteract them.

## How This Section Relates to the Rest

- The **[Modeling](../modeling/README.md)** section explains how to estimate probabilities accurately enough to find value bets
- The **[Strategy](../strategy/README.md)** section explains how to size bets, shop for prices, and manage accounts once you have a model
- The **[Sport-Specific](../sport-specific/README.md)** guides apply these foundations to each sport's particular structure
- The **[Glossary](../glossary.md)** defines every term used across all documents — consult it whenever a concept is unfamiliar
