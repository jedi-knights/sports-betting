# sports-betting — Claude Instructions

## Documentation Style

When writing or editing any Markdown file in this repository, cross-link related documents as much as possible. Every time a concept, model, or topic is mentioned that has its own document in `docs/`, link to it. This makes navigation easy on GitHub and helps a reader who is new to the field follow the thread between ideas.

- Prefer relative links: `[calibration](../calibration.md)` not an absolute path
- Link on first mention within each section, not every occurrence
- The glossary (`docs/glossary.md`) is the anchor reference — link to it when introducing a term that appears there

## Repository Context

This is a research and tooling repository for sports betting models. The owner is new to the field. When writing documentation, explain concepts clearly and define terms — do not assume prior knowledge of sports betting, statistics, or machine learning.

## Docs Structure

```
docs/
  glossary.md              # term definitions — the anchor reference
  value-betting.md         # core concept: positive EV
  odds-and-markets.md      # odds formats, bet types, vig
  calibration.md           # probability calibration — most important model property
  backtesting.md           # walk-forward validation, avoiding lookahead bias
  bankroll-management.md   # Kelly Criterion, bet sizing
  monte-carlo.md           # simulation techniques
  market-efficiency.md     # closing line value, sharp vs. square
  data-and-features.md     # data sources, feature engineering
  emerging.md              # RL, real-time inference, graph networks
  models/
    poisson.md             # goal-scoring model for soccer
    elo.md                 # dynamic team strength ratings
    logistic-regression.md # baseline classification model
    quantile-regression.md # spread/totals distribution modeling
    ml-methods.md          # XGBoost, Random Forests, ensembles
```
