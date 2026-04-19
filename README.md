# sports-betting

General purpose code and documentation for building, evaluating, and applying sports betting models.

![Go](https://github.com/jedi-knights/sports-betting/actions/workflows/go.yml/badge.svg)
![Python](https://github.com/jedi-knights/sports-betting/actions/workflows/python.yml/badge.svg)

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

- **Go** 1.22+ — backend services and domain logic
- **Python** 3.12+ with [uv](https://docs.astral.sh/uv/) — CLI tooling and modeling
- **Docker** + **Docker Compose** — local infrastructure (PostgreSQL)

## Installation

```bash
git clone https://github.com/jedi-knights/sports-betting.git
cd sports-betting
```

Set up Go dependencies:

```bash
go mod tidy
```

Set up the Python CLI:

```bash
uv sync
```

Copy and fill in environment variables:

```bash
cp .env.example .env
```

Start the local database:

```bash
docker compose up -d
```

> **Note:** `docker compose down` stops containers but preserves data in the `postgres_data` named volume. Use `docker compose down -v` to also remove the volume and reset all data.

## Usage

The `bet` CLI is the primary interface for fetching data, running backtests, and paper trading.

```bash
# Show available commands
uv run bet --help
```

### `bet fetch` — Download league data to CSV

Fetches completed match results from free public sources and writes them to a CSV file. The output format is compatible with `bet backtest --data`.

```bash
uv run bet fetch --league <league> [--output <path>] [--history]
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--league` | Yes | — | League to fetch (see table below) |
| `--output` | No | `<league>.csv` | Output file path |
| `--history` | No | off | Fetch all historical seasons instead of the current season only |

**Valid `--league` values:**

| Value | League | Current Season | History coverage |
|-------|--------|---------------|-----------------|
| `ecnl-girls` | ECNL Girls | 2025-26 | 2015-16 → present |
| `ecnl-boys` | ECNL Boys | 2025-26 | 2017-18 → present |
| `ecrl-girls` | ECRL Girls | 2025-26 | 2021-22 → present |
| `ecrl-boys` | ECRL Boys | 2025-26 | 2021-22 → present |
| `ecnl` | All four ECNL/ECRL leagues | 2025-26 | All above combined |
| `nwsl` | National Women's Soccer League | Current | — |
| `mls` | Major League Soccer | Current | 2013 → present (with `--history`) |
| `wpsl` | Women's Premier Soccer League | Current | — |
| `usl-super-league` | USL Super League | Current | — |

**Examples:**

```bash
# Current ECNL Girls season → ecnl-girls.csv
uv run bet fetch --league ecnl-girls

# Full ECNL Girls history → data/ecnl_girls_full.csv
uv run bet fetch --league ecnl-girls --history --output data/ecnl_girls_full.csv

# All four ECNL/ECRL leagues, current season
uv run bet fetch --league ecnl --output data/ecnl.csv

# MLS full history
uv run bet fetch --league mls --history --output data/mls.csv
```

## Configuration

All configuration is read from environment variables. Copy `.env.example` to `.env` and fill in values. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `sportsbetting` | Database name |
| `POSTGRES_USER` | `sportsbetting` | Database user |
| `POSTGRES_PASSWORD` | `changeme` | Database password |
| `POSTGRES_PORT` | `5433` | Exposed port on the host |
| `PAPER_TRADE_MIN_EDGE` | `0.03` | Minimum edge (3%) before recording a paper bet |
| `PAPER_TRADE_KELLY_FRACTION` | `0.25` | Kelly fraction for paper bet sizing |
| `PAPER_TRADE_STARTING_BANKROLL` | `10000` | Starting paper bankroll in USD |

See `.env.example` for the full list.

## Development

Run Go tests:

```bash
go test ./...
```

Run Python tests:

```bash
uv run pytest
```

The Go module is at the repository root. Domain packages live under `internal/`. Python source lives under `src/bet/`; Python tests live under `tests/`.

## Contributing

Open an issue to discuss changes before submitting a pull request. There is no `CONTRIBUTING.md` yet — one will be added as the project matures.

## License

No license defined yet. A license will be added before any public release.
