# Platform Architecture

This document defines the bounded contexts, architectural decisions, and implementation plan for the sports betting platform. It is the primary reference for all implementation work and should be updated as decisions evolve.

## Documents in This Section

| Document | Description |
|----------|-------------|
| [Bounded Contexts & Implementation Plan](README.md) | This file — context definitions, architectural decisions, implementation checklist |
| [Data Models](data-models.md) | Canonical type definitions for all contexts (Go + Python) |

## Architectural Decisions

### Language Split
- **Go** — all services, APIs, and data pipelines where speed and concurrency matter
- **Python** — CLI tooling, statistical modeling, machine learning, and backtesting analysis

### Interface Strategy
Both a CLI and a service/API are first-class targets. The CLI uses Python for direct access to the modeling stack. The service layer uses Go and exposes HTTP APIs that the CLI can optionally call, enabling the same logic to power both interactive use and automated systems.

### Simulation-First
Development proceeds in this order: backtesting on historical data → paper trading against live odds without real money → live execution with real bookmaker accounts. Live bookmaker integration is an **explicit future goal**, not an afterthought. Every context that touches external data or bet placement defines a port interface from day one so the real implementation can be substituted without rewriting the domain.

### Bookmaker Integration Assumption
All interactions with bookmakers — odds ingestion, bet placement, account management — are accessed exclusively through interfaces. No domain logic ever calls a bookmaker API directly. This makes it possible to run the full pipeline with static test data, a mock, or a real API without changing any core logic.

---

## Bounded Contexts

### 1. Market Data
**Responsible for**: ingesting, normalizing, and storing bookmaker odds and line movement. Has no knowledge of models or betting strategy.

| Layer | Language | Notes |
|-------|----------|-------|
| Domain types | Go | `Market`, `Line`, `Book`, `Odds` |
| Port: `OddsProvider` | Go | Interface satisfied by static files, mock, or live bookmaker client |
| Port: `LineStore` | Go | Interface for persisting and querying odds history |
| Adapters | Go | CSV/static (backtesting), mock (paper trading), bookmaker API (future) |

Key behaviors:
- Convert any odds format (American, decimal, fractional) to implied probability
- Track line movement over time
- Devig (remove bookmaker margin) to extract true market probability

---

### 2. Statistical Modeling
**Responsible for**: generating probability estimates for game outcomes from historical features. Has no knowledge of bookmakers or bet sizing.

| Layer | Language | Notes |
|-------|----------|-------|
| Domain types | Python | `Prediction`, `ProbabilityEstimate`, `FeatureSet` |
| Protocol: `Model` | Python | `predict(features) -> ProbabilityEstimate` |
| Implementations | Python | Elo, Poisson, LogisticRegression, XGBoost, Ensemble |
| Feature pipeline | Python | Per-sport feature extraction and transformation |

Key behaviors:
- Each model implements the same `Model` protocol — swappable without changing the pipeline
- Feature sets are sport-specific but follow a common schema
- Models output probabilities, not class labels

---

### 3. Calibration
**Responsible for**: wrapping a model and adjusting its raw probability outputs to be better calibrated. Depends on Statistical Modeling; feeds into Value Analysis.

| Layer | Language | Notes |
|-------|----------|-------|
| Domain types | Python | `CalibratedModel`, `CalibrationCurve`, `BrierScore` |
| Protocol: `Calibrator` | Python | `fit(probs, outcomes)` / `transform(probs)` |
| Implementations | Python | Platt scaling, isotonic regression |

Key behaviors:
- Wraps any `Model` and applies a post-hoc correction layer
- Evaluates calibration quality via reliability diagrams, Brier score, and log-loss
- Calibration is always applied before value analysis — never compare raw model output to market odds

---

### 4. Value Analysis
**Responsible for**: comparing calibrated model probabilities against market-implied probabilities to surface positive expected value opportunities.

| Layer | Language | Notes |
|-------|----------|-------|
| Domain types | Go + Python | `ValueBet`, `EdgeEstimate`, `ExpectedValue` |
| Core formula | Both | `EV = (model_prob × decimal_odds) − 1` |
| Port: `ValueDetector` | Python | `detect(prediction, line) -> ValueBet \| None` |

Key behaviors:
- EV is computed for every model prediction against every available line
- Minimum edge threshold is configurable and applied before a `ValueBet` is emitted
- Closing line value (CLV) is tracked separately to evaluate model quality independent of outcomes

---

### 5. Bankroll Management
**Responsible for**: computing stake sizes given an edge estimate and current bankroll. Has no knowledge of markets or models.

| Layer | Language | Notes |
|-------|----------|-------|
| Domain types | Go + Python | `Bankroll`, `BetSizing`, `KellyFraction` |
| Protocol: `Sizer` | Both | `size(ev, odds, bankroll) -> Stake` |
| Implementations | Both | Full Kelly, ½ Kelly, ¼ Kelly, flat unit |

Key behaviors:
- Kelly Criterion computes the mathematically optimal fraction given edge and odds
- Fractional Kelly reduces variance at the cost of ~25% optimal growth (industry standard)
- Sizer is always applied after value detection — never bet without a size rule

---

### 6. Bet Tracking
**Responsible for**: recording all bet signals, outcomes, and performance metrics. The system of record for P&L and model evaluation.

| Layer | Language | Notes |
|-------|----------|-------|
| Domain types | Go | `Bet`, `Outcome`, `BetResult`, `PerformanceReport` |
| Port: `BetStore` | Go | Interface for persisting and querying bet history |
| Adapters | Go | In-memory (backtesting), file-based CSV/JSON, database (future) |
| Metrics | Python | ROI, yield, CLV, max drawdown, Sharpe ratio |

Key behaviors:
- Every signal emitted by Value Analysis is recorded, whether acted on or not
- Outcomes are resolved after each game and linked back to the original signal
- Performance reports include both paper and live bets (tagged separately)

---

### 7. Backtesting
**Responsible for**: replaying historical data through the complete pipeline — data → model → calibrate → value → size → record — without lookahead bias. Produces performance reports for model validation.

| Layer | Language | Notes |
|-------|----------|-------|
| Harness | Python | Walk-forward validation engine |
| Data loader | Python | Historical odds + outcomes from static sources |
| Pipeline runner | Python | Wires all contexts together in the correct order |
| CLI | Python | `bet backtest --sport nfl --season 2023` |

Key behaviors:
- Walk-forward only: model is never trained on data from the period being evaluated
- Realistic odds assumptions: use closing line, not opening line, for EV calculation
- All results feed into Bet Tracking for unified performance reporting

---

### 8. Paper Trading *(future, after backtesting is validated)*
**Responsible for**: running the pipeline against live odds without placing real money bets. Proves the live pipeline works before capital is at risk.

| Layer | Language | Notes |
|-------|----------|-------|
| Odds polling | Go | Polls live odds via `OddsProvider` interface |
| Paper bet service | Go | Records paper bets via `BetStore` interface |
| CLI | Python | `bet paper-trade --sport nfl` |
| API | Go | Endpoints for monitoring open paper positions |

---

### 9. Live Execution *(future)*
**Responsible for**: placing real bets with bookmakers. Implemented by satisfying the same interfaces already defined in earlier phases — the only new code is adapter implementations.

| Layer | Language | Notes |
|-------|----------|-------|
| Port: `BookmakerClient` | Go | The primary live integration interface |
| Port: `AccountManager` | Go | Balance, limits, session management |
| Adapters | Go | One per bookmaker (DraftKings, Pinnacle, etc.) |

The entire domain stack above this layer is unchanged when switching from paper to live. No domain logic is modified.

---

## Implementation Plan

Work through phases in order. Check off each item when complete. Do not advance to the next phase until the current phase has passing tests.

### Phase 1 — Foundation & Market Data

**Project scaffold**
- [x] Initialize Go module (`go.mod`) at repository root
- [x] Initialize Python project (`pyproject.toml` + `uv`) for CLI tooling
- [x] Create `.gitignore` covering: `data/`, `.env`, `*.env`, build artifacts, `__pycache__`, `.venv`
- [x] Create `.env.example` documenting all required environment variables with placeholder values

**Infrastructure (Docker)**
- [x] Create `docker-compose.yml` at repository root with a PostgreSQL service and named volume
- [x] Declare `postgres_data` named volume in `docker-compose.yml` for database persistence
- [x] Add PostgreSQL healthcheck so dependent services wait for readiness
- [x] Verify `docker compose up` starts Postgres and persists data across `docker compose down` / `up` cycles

**Market Data domain**
- [x] Define odds format types in Go: `AmericanOdds`, `DecimalOdds`, `FractionalOdds`, `ImpliedProbability`
- [x] Implement odds conversion functions: American → Decimal → Implied Probability → Decimal
- [x] Define `Market`, `Line`, `Book`, `Odds` domain types in Go
- [x] Implement devig (Shin method or basic proportional removal) to extract true market probability
- [x] Define `OddsProvider` port interface in Go
- [x] Define `LineStore` port interface in Go
- [x] Implement `StaticOddsProvider` (reads from CSV/JSON files) for use in backtesting
- [x] Implement in-memory `LineStore` for testing
- [x] Unit tests for all odds conversion and devig logic

### Phase 2 — Statistical Modeling

- [x] Define `ProbabilityEstimate` and `FeatureSet` types (Python)
- [x] Define `Model` protocol (Python): `fit(data)` / `predict(features) -> ProbabilityEstimate`
- [x] Define `FeatureExtractor` protocol (Python): per-sport feature pipeline abstraction
- [x] Implement Elo model (NFL baseline): rating update, expected score, win probability
- [x] Implement Elo feature extractor for NFL
- [x] Implement Elo feature extractor for NBA (rest days default 2.0, no weather features)
- [x] Implement Elo feature extractor for MLB (rest days default 1.0, lower K-factor for high-variance sport)
- [x] Implement Elo feature extractor for NHL (rest days default 2.0, binary outcomes including OT/SO wins)
- [x] Implement Poisson model: attack/defense strength estimation, Dixon-Coles correction
- [x] Implement Poisson feature extractor for soccer
- [x] Implement logistic regression model: log-loss training objective, L2 regularization
- [x] Implement gradient boosting model (`GradientBoostingClassifier`): non-linear, no feature scaling required; see [`docs/modeling/models/ml-methods.md`](../modeling/models/ml-methods.md)
- [x] Implement ensemble model: averages probability outputs from any list of `Model` instances; re-normalises to sum 1.0
- [x] Implement quantile regression model: fits median + spread; converts margin distribution to win probability via normal CDF; `predict_quantiles()` available for spread/totals markets; see [`docs/modeling/models/quantile-regression.md`](../modeling/models/quantile-regression.md)
- [x] Unit tests for each model and feature extractor

### Phase 3 — Calibration

- [x] Define `CalibratedModel` wrapper (Python): implements `Model` protocol, applies correction
- [x] Define `Calibrator` protocol: `fit(probs, outcomes)` / `transform(probs) -> probs`
- [x] Implement Platt scaling calibrator
- [x] Implement isotonic regression calibrator
- [x] Implement Brier score and log-loss evaluation utilities
- [x] Implement reliability diagram (calibration curve) generation
- [x] Unit tests for calibrators

### Phase 4 — Value Analysis

- [x] Define `ValueBet` and `EdgeEstimate` types (Python + Go)
- [x] Implement EV calculation: `ev = (model_prob × decimal_odds) − 1`
- [x] Define `ValueDetector` protocol (Python)
- [x] Implement minimum-edge `ValueDetector` with configurable threshold
- [x] Implement CLV tracking: compare bet odds to closing line at game time
- [x] Unit tests for EV calculation and CLV tracking

### Phase 5 — Bankroll Management

- [x] Define `Bankroll` and `BetSizing` types
- [x] Define `Sizer` interface/protocol (Python + Go)
- [x] Implement full Kelly Criterion
- [x] Implement ½ Kelly and ¼ Kelly
- [x] Implement flat unit staking
- [x] Add ruin probability estimator: given Kelly fraction, bankroll, and edge, estimate drawdown risk
- [x] Unit tests for all sizers

### Phase 6 — Bet Tracking

- [x] Define `Bet`, `BetStatus`, `Outcome`, `BetResult` domain types (Go)
- [x] Define `BetStore` port interface (Go)
- [x] Implement in-memory `BetStore` for backtesting and tests
- [x] Implement file-based `BetStore` (CSV output)
- [x] Implement performance report: ROI, yield, max drawdown, Sharpe ratio, win rate
- [x] Implement CLV resolution: update each bet record with the closing line after game time
- [x] Unit tests for bet recording and performance report accuracy

### Phase 7 — Backtesting Harness

- [x] Implement walk-forward validation engine (Python): rolling train/test windows with configurable lookback
- [x] Implement historical data loader: reads odds + outcomes from static files
- [x] Implement full pipeline runner: data → model → calibrate → value → size → record
- [x] Add lookahead bias guard: assert no future data is accessible at prediction time
- [x] Implement CLI command: `bet backtest --sport nfl --data games.csv --model elo`
- [x] Implement CLI command: `bet backtest --sport soccer --data games.csv --model poisson`
- [x] Implement CLI command: supports `--sport [nfl|nba|mlb|nhl|soccer]` and `--model [elo|logistic|poisson|gradient_boosting|quantile|ensemble]`
- [x] Generate end-of-run performance report to stdout and JSON file
- [x] Integration tests: full pipeline for every sport × default model combination (`tests/integration/test_backtest_pipeline.py`)

### Phase 8 — Paper Trading *(after backtesting is validated)*

**Simulated Bookmaker**
- [x] Define `SimulatedBookmakerClient` implementing the `BookmakerClient` interface
- [x] Implement configurable margin: apply overround to all offered odds
- [x] Implement line movement: shift offered odds after each accepted bet proportional to stake size
- [x] Implement bet rejection: reject bets placed on expired offers or lines that have moved since the offer
- [x] Implement partial fills: cap accepted stake at configured `max_stake`; return remainder unfilled
- [x] Implement account limiting: after N winning bets, reduce `max_stake` to a floor value
- [x] Unit tests for each simulated behaviour (movement, rejection, partial fill, limiting)

**Go services**
- [x] Implement Go service: `market-data` — polls `OddsProvider` on a schedule, stores in `LineStore`
- [x] Implement Go service: `paper-trade` — wires `SimulatedBookmakerClient` into the full pipeline; records paper bets
- [x] Expose REST API: `GET /paper/bets`, `GET /paper/performance`
- [x] Implement CLI command: `bet paper-trade --sport nfl` (connects to the Go service)
- [x] Integration test: full paper trading loop end-to-end with `SimulatedBookmakerClient`
- [x] Unit tests: HTTP handlers (`GET /paper/bets`, `GET /paper/performance`), bet resolution, and `envOr` helper (`services/paper-trade/main_test.go`)

**Containerization**
- [x] Write `services/market-data/Dockerfile` (multi-stage: builder + distroless)
- [x] Write `services/paper-trade/Dockerfile` (multi-stage: builder + distroless)
- [x] Add `market-data` and `paper-trade` services to `docker-compose.yml`
- [x] Declare named volume for `LineStore` persistence (if file-based) or wire to Postgres
- [x] Declare named volume for `BetStore` persistence
- [x] Verify `docker compose up` brings up the full stack; data survives `down` / `up`

### Phase 9 — Live Execution *(after paper trading is validated)*

- [x] Define `AccountManager` interface (Go): balance, limits, session state
- [x] Implement first real `BookmakerClient` adapter (Pinnacle recommended as the sharp-book reference)
- [x] Implement `AccountManager` adapter for that bookmaker
- [x] Add bet placement safety checks: maximum stake cap, account balance floor, duplicate bet guard
- [x] Integration test: end-to-end live placement on a small stake with a single bookmaker
- [x] Smoke test: confirm CLV tracking works against a real closing line

### Phase 10 — CI and Quality

- [x] Add `.github/workflows/go.yml`: runs `go vet` and `go test ./...` on push and pull requests
- [x] Add `.github/workflows/python.yml`: runs `ruff check` and `pytest` on push and pull requests
- [x] Add `ruff` configuration to `pyproject.toml` (line-length, target Python version, rule set)

---

## Context Map

```
Historical Data → [StaticOddsProvider]
                        │
                        ▼
              [Market Data Context]
                        │
                        ▼
            [Statistical Modeling Context]
                        │
                        ▼
              [Calibration Context]
                        │
                        ▼
              [Value Analysis Context]
                        │
                  ┌─────┴──────┐
                  ▼            ▼
        [Bankroll Mgmt]  [Bet Tracking]
                  │            │
                  └─────┬──────┘
                        ▼
                 [Backtesting / 
               Paper Trading /
               Live Execution]
```

Live bookmaker APIs enter only at the `OddsProvider` and `BookmakerClient` ports — everything above that line is unchanged between simulation and live modes.
