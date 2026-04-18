# sports-betting

General purpose code and documentation for building, evaluating, and applying sports betting models.

## Table of Contents

- [Overview](#overview)
- [Documentation](#documentation)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Overview

This repository houses research, implementations, and tooling for sports betting models. The core goal is identifying mispriced odds by comparing model-estimated probabilities against bookmaker-implied probabilities — a technique known as value betting. Modern calibration research shows that optimizing for probability calibration rather than raw accuracy produces significantly higher returns: calibration-focused models have demonstrated +34.69% returns versus -35.17% for accuracy-only approaches.

## Documentation

All research and reference material lives under [`docs/`](docs/). Start with the [Glossary](docs/glossary.md) for term definitions, then follow the section reading order below.

| Section | Description |
|---------|-------------|
| [Foundations](docs/foundations/README.md) | Core concepts: odds formats, value betting, market efficiency, variance, psychology |
| [Modeling](docs/modeling/README.md) | Building and evaluating models: calibration, backtesting, features, weather, Monte Carlo |
| [Modeling — Models](docs/modeling/models/README.md) | Model deep-dives: Poisson, Elo, logistic regression, quantile regression, ML methods |
| [Strategy](docs/strategy/README.md) | Execution: bankroll management, line shopping, props, arbitrage, hedging, playoff modeling |
| [Sport-Specific](docs/sport-specific/README.md) | Per-sport guides: NFL, NBA, MLB, NHL, Soccer |
| [Architecture](docs/architecture/README.md) | Bounded contexts, data models, and implementation plan for the platform |

**Recommended starting point for newcomers:** [Foundations → Odds and Markets](docs/foundations/odds-and-markets.md)

## Features

- **Value betting framework** — compare estimated outcome probabilities against bookmaker-implied odds to surface positive expected value opportunities
- **Classical statistical models** — Poisson distribution for goal/score markets, Elo ratings for team strength estimation, logistic regression for win probability
- **Machine learning methods** — XGBoost, Random Forests, and ensemble techniques (reported 91–94% accuracy on select datasets)
- **Calibration tooling** — evaluate and optimize model calibration, not just predictive accuracy
- **Quantile regression** — target spread and totals markets where point spreads explain ~86% of outcome variability
- **Bankroll management** — Kelly Criterion and Fractional Kelly (½, ¼) bet-sizing utilities
- **Monte Carlo simulation** — generate probability distributions across thousands of game scenarios

## Requirements

N/A — no implementation exists yet. Requirements will be defined as the project takes shape.

## Installation

N/A — no installable package exists yet.

## Usage

N/A — no runnable code exists yet.

## Configuration

N/A — no configuration options defined yet.

## Development

Clone the repository:

```bash
git clone https://github.com/jedi-knights/sports-betting.git
cd sports-betting
```

No build or test steps are defined yet. Contributions that establish the project structure are welcome.

## Contributing

Open an issue to discuss changes before submitting a pull request. There is no `CONTRIBUTING.md` yet — one will be added as the project matures.

## License

No license defined yet. A license will be added before any public release.
