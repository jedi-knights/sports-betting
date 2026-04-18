# Modeling

The documents in this section cover how to build, evaluate, and validate predictive models for sports betting. They assume familiarity with the concepts in [Foundations](../foundations/README.md) — particularly what a probability estimate is and why calibration matters more than accuracy.

## Overview

A sports betting model's job is to estimate the true probability of each outcome more accurately than the bookmaker's implied probability. This section covers the full pipeline: choosing the right model architecture, engineering the right features, evaluating whether your model is trustworthy, and validating it against historical data without cheating.

## Documents

### Core Methodology

**[Calibration](calibration.md)**
The most important document in this section. Explains the difference between accuracy (does the model pick the right team?) and calibration (are the probabilities trustworthy?). A 2024 meta-analysis found calibration-optimized models returned +34.69% ROI vs. -35.17% for accuracy-optimized models — a 70-point gap. Covers reliability diagrams, Brier score, log-loss, and the two main post-hoc calibration methods: Platt scaling (for most models) and isotonic regression (for tree-based models). Read this before building any model.

**[Backtesting](backtesting.md)**
How to evaluate a model against historical data without fooling yourself. Covers walk-forward validation (the only correct method for time-series data), lookahead bias and how to accidentally introduce it, realistic odds assumptions, bet selection logic, and the full set of metrics to track — ROI, yield, maximum drawdown, Sharpe ratio, and closing line value. Includes a practical pre-flight checklist for trusting backtest results.

**[Data and Features](data-and-features.md)**
Feature engineering is consistently more important than algorithm choice in sports prediction. Covers the major data sources for each sport, the categories of features that matter (team strength, recent form, rest/travel, situational factors, injuries), and the engineering principles that prevent common mistakes: opponent adjustment, recency weighting, avoiding lookahead bias, and handling missing data. The definitive reference for what to put into your model.

**[Weather Modeling](weather-modeling.md)**
Weather has quantifiable, consistent effects on scoring in outdoor sports — particularly NFL and MLB. Covers wind speed and direction effects on NFL totals (>20 mph reduces total by 3–5 points), precipitation and temperature effects, park factor interactions in MLB, and how to build a weather feature pipeline against public forecast APIs. Includes a recommended feature set for NFL totals models.

**[Monte Carlo Simulation](monte-carlo.md)**
When analytical probability formulas become intractable — season simulations, correct-score markets, series win probability, parlay correlation — Monte Carlo generates the answer by running the scenario thousands of times. Covers the structure of a simulation, convergence rates, applications to totals markets, futures bracket modeling, and bankroll ruin estimation. Includes notes on variance reduction techniques for computationally expensive simulations.

**[Emerging Methods](emerging.md)**
A forward-looking survey of techniques not yet mainstream in practitioner toolkits: multimodal data integration (tracking data, NLP on news feeds), reinforcement learning for bet sizing, real-time in-game inference architecture, portfolio-based bet sizing, causal inference, and graph neural networks. Useful for understanding where the field is heading; not required for building a first model.

### Model Deep-Dives

The [`models/`](models/README.md) subdirectory contains detailed implementation guides for each modeling approach.

| Model | Best for | Key strength |
|-------|----------|--------------|
| [Poisson](models/poisson.md) | Soccer goals, NHL goals | Mechanistic; produces full scoreline distributions |
| [Elo](models/elo.md) | Relative team strength, any sport | Simple, interpretable, handles small samples |
| [Logistic Regression](models/logistic-regression.md) | Win probability, baseline model | Well-calibrated; interpretable coefficients |
| [Quantile Regression](models/quantile-regression.md) | Spreads and totals | Models full outcome distribution, not just mean |
| [ML Methods](models/ml-methods.md) | High-feature-count tabular data | Captures non-linear interactions |

## Recommended Build Sequence

For a first model, work through the documents in this order:

1. Read **Calibration** — understand what you are optimizing for
2. Read **Data and Features** — understand what inputs to use
3. Build a **Logistic Regression** baseline
4. Set up **Backtesting** with walk-forward validation
5. Evaluate calibration; apply post-hoc correction if needed
6. Add **XGBoost** as a second model (see ML Methods); compare calibrated performance
7. Add **Monte Carlo** for futures and series pricing
8. Add **Weather** features for NFL/MLB totals

## How This Section Relates to the Rest

- Start with **[Foundations](../foundations/README.md)** before reading here — especially Value Betting and Calibration concepts
- The **[Strategy](../strategy/README.md)** section covers what to do once a model produces probability estimates: sizing bets, shopping for prices, managing accounts
- The **[Sport-Specific](../sport-specific/README.md)** guides specify which models and features apply to each sport
