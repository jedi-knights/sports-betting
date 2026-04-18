# Data Models

Conceptual entity models for each bounded context. These diagrams are the canonical reference for what data exists and how it relates — implementation files in Go and Python derive from these shapes, not the other way around.

Each context owns its entities. When a context needs data from another context it references it by ID only — it never shares a type definition across the boundary.

---

## Market Data

The foundational context. Every other context either reads from Market Data or produces data that eventually flows back into it (e.g., closing lines resolving value bets).

```mermaid
erDiagram
    BOOK {
        string id
        string name
        string type
    }
    EVENT {
        string id
        string sport
        string home_team
        string away_team
        timestamp starts_at
        string season
        int    week
        string venue
    }
    MARKET {
        string    id
        string    event_id
        string    type
        timestamp created_at
    }
    LINE {
        string    id
        string    market_id
        string    book_id
        string    side
        string    label
        int       american_odds
        float     decimal_odds
        float     raw_implied_prob
        float     implied_prob
        float     spread
        float     total
        timestamp recorded_at
        boolean   is_closing
    }

    EVENT    ||--|{ MARKET : "has"
    MARKET   ||--|{ LINE   : "has"
    BOOK     ||--o{ LINE   : "prices"
```

| Entity | Field | Note |
|--------|-------|------|
| BOOK | type | One of: `sharp`, `soft`, `exchange` |
| EVENT | sport | One of: `nfl`, `nba`, `mlb`, `nhl`, `soccer` |
| EVENT | week | Populated for NFL only; null for all other sports |
| MARKET | type | One of: `moneyline`, `spread`, `total`, `player_prop` |
| LINE | side | One of: `home`, `away`, `draw`, `over`, `under` |
| LINE | raw_implied_prob | Implied probability before removing bookmaker margin (overround) |
| LINE | implied_prob | Devigged — the market's true probability estimate; always in [0, 1] |
| LINE | spread | Populated for spread markets only; null otherwise |
| LINE | total | Populated for totals markets only; null otherwise |
| LINE | is_closing | True only for the line recorded at or nearest to game time |

**Ports (behavior contracts, not data shapes)**

- `OddsProvider` — fetches events, markets, and lines from an external source; implemented by a static file reader for backtesting and a live bookmaker client for paper trading and live execution
- `LineStore` — persists and queries line history; implemented in-memory for tests and against PostgreSQL for running services

---

## Statistical Modeling

Produces probability estimates from historical features. Has no knowledge of bookmakers, odds, or money.

```mermaid
erDiagram
    FEATURE_SET {
        string    event_id
        string    sport
        string    home_team
        string    away_team
        timestamp as_of
    }
    ACTUAL_OUTCOME {
        string    event_id
        int       home_score
        int       away_score
        timestamp final_at
    }
    TRAINING_EXAMPLE {
        string feature_set_id
        string outcome_id
    }
    PROBABILITY_ESTIMATE {
        string    event_id
        string    model_id
        timestamp generated_at
        float     home_win
        float     away_win
        float     draw
    }

    FEATURE_SET      ||--|| TRAINING_EXAMPLE      : "input to"
    ACTUAL_OUTCOME   ||--|| TRAINING_EXAMPLE      : "label for"
    FEATURE_SET      ||--|| PROBABILITY_ESTIMATE  : "produces"
```

| Entity | Field | Note |
|--------|-------|------|
| FEATURE_SET | as_of | Hard cutoff: no feature may be derived from data after this timestamp; enforces the lookahead bias guard |
| PROBABILITY_ESTIMATE | draw | Null for sports without a draw outcome (NFL, NBA, MLB) |
| PROBABILITY_ESTIMATE | home_win + away_win + draw | Must sum to 1.0 |
| PROBABILITY_ESTIMATE | model_id | Identifies which model produced the estimate; used for calibration tracking |

**Ports**

- `Model` — fits on training examples and predicts a probability estimate for a feature set; implemented by Elo, Poisson, logistic regression, XGBoost, and ensemble variants
- `FeatureExtractor` — computes a feature set for a given event as of a given timestamp; one implementation per sport

---

## Calibration

Wraps a probability estimate and corrects its raw probabilities to be better calibrated. Depends on Statistical Modeling; feeds into Value Analysis.

```mermaid
erDiagram
    PROBABILITY_ESTIMATE {
        string event_id
        string model_id
    }
    CALIBRATED_ESTIMATE {
        string raw_estimate_id
        string calibrator_id
        float  calibrated_home_win
        float  calibrated_away_win
        float  calibrated_draw
    }
    CALIBRATION_CURVE {
        string model_id
        string calibrator_id
        float  brier_score
        float  log_loss
    }

    PROBABILITY_ESTIMATE ||--||  CALIBRATED_ESTIMATE : "corrected by"
    CALIBRATION_CURVE    }o--||  PROBABILITY_ESTIMATE : "evaluates"
```

| Entity | Field | Note |
|--------|-------|------|
| CALIBRATED_ESTIMATE | raw_estimate_id | Foreign reference into Statistical Modeling context — ID only |
| CALIBRATED_ESTIMATE | calibrated_draw | Null for sports without a draw outcome |
| CALIBRATION_CURVE | brier_score | Lower is better; a perfectly calibrated model scores 0 |
| CALIBRATION_CURVE | log_loss | Lower is better; the training objective for logistic regression |

**Ports**

- `Calibrator` — fits on a held-out set of raw probabilities and outcomes, then transforms new raw probabilities into corrected ones; implemented by Platt scaling and isotonic regression

---

## Value Analysis

Compares calibrated model probabilities against market-implied probabilities to surface positive expected value opportunities. Receives data from both Market Data and Calibration.

```mermaid
erDiagram
    VALUE_BET {
        string    event_id
        string    line_id
        string    market_type
        string    side
        string    book
        float     model_prob
        float     market_implied_prob
        float     decimal_odds
        float     ev
        float     edge
        timestamp detected_at
    }
    CLV_RECORD {
        string    bet_id
        float     bet_implied_prob
        float     closing_implied_prob
        float     clv
        timestamp resolved_at
    }

    VALUE_BET ||--o| CLV_RECORD : "resolved by"
```

| Entity | Field | Note |
|--------|-------|------|
| VALUE_BET | line_id | Foreign reference into Market Data context — ID only |
| VALUE_BET | model_prob | The calibrated probability; never raw model output |
| VALUE_BET | market_implied_prob | Devigged implied probability from the line |
| VALUE_BET | ev | `(model_prob × decimal_odds) − 1`; must be positive to qualify as a value bet |
| VALUE_BET | edge | `model_prob − market_implied_prob`; must exceed the configured minimum threshold |
| CLV_RECORD | bet_id | Foreign reference into Bet Tracking context — ID only |
| CLV_RECORD | clv | `closing_implied_prob − bet_implied_prob`; positive means bet was placed at better-than-closing odds — the long-run signal of genuine edge |

---

## Bankroll Management

Computes stake sizes from an edge and current bankroll. Has no knowledge of specific markets, events, or models.

```mermaid
erDiagram
    BANKROLL {
        float  total
        float  available
        string currency
    }
    BET_SIZING {
        string strategy
        float  stake
        float  fraction
        float  kelly_fraction
    }

    BANKROLL ||--o{ BET_SIZING : "constrains"
```

| Entity | Field | Note |
|--------|-------|------|
| BANKROLL | available | `total` minus all stakes reserved for open (unresolved) bets |
| BET_SIZING | strategy | One of: `full_kelly`, `half_kelly`, `quarter_kelly`, `flat` |
| BET_SIZING | kelly_fraction | The raw Kelly output before applying the fractional multiplier |
| BET_SIZING | fraction | `stake / bankroll.total`; the actual portion of bankroll being risked |

**Ports**

- `Sizer` — given an EV, decimal odds, and bankroll, returns a bet sizing; implemented by full Kelly, fractional Kelly variants, and flat unit

---

## Bet Tracking

Records every bet signal and its eventual outcome. The system of record for all performance reporting. Receives data from Value Analysis and Bankroll Management.

```mermaid
erDiagram
    BET {
        string    id
        string    value_bet_id
        string    event_id
        string    market_type
        string    side
        string    book
        float     decimal_odds
        float     stake
        float     to_win
        string    status
        string    mode
        timestamp placed_at
        timestamp resolved_at
        string    external_id
    }
    BET_RESULT {
        string bet_id
        float  profit
        float  roi
        float  clv
    }
    PERFORMANCE_REPORT {
        string period
        string mode
        int    total_bets
        int    won_bets
        int    lost_bets
        int    void_bets
        float  total_staked
        float  total_profit
        float  roi
        float  win_rate
        float  avg_clv
        float  max_drawdown
        float  sharpe_ratio
    }

    BET         ||--||  BET_RESULT         : "resolved as"
    BET_RESULT  }o--||  PERFORMANCE_REPORT : "aggregated into"
```

| Entity | Field | Note |
|--------|-------|------|
| BET | value_bet_id | Foreign reference into Value Analysis context — ID only |
| BET | status | One of: `pending`, `open`, `won`, `lost`, `void`, `paper` |
| BET | mode | One of: `backtest`, `paper`, `live`; paper and backtest bets never involve real money |
| BET | to_win | `stake × (decimal_odds − 1)` |
| BET | external_id | Bookmaker's reference number; empty for `backtest` and `paper` mode bets |
| BET | resolved_at | Null until the game is final |
| BET_RESULT | profit | Positive for wins, negative for losses, zero for voids |
| BET_RESULT | clv | Null until the closing line is known; populated by a CLV_RECORD from Value Analysis |
| PERFORMANCE_REPORT | period | A time window label (e.g., `"2023-nfl"`, `"all-time"`) |

**Ports**

- `BetStore` — persists and queries bets and performance reports; implemented in-memory for backtesting and against PostgreSQL for running services

---

## Backtesting

Drives the full pipeline over historical data to validate model and strategy performance before any real money is involved.

```mermaid
erDiagram
    BACKTEST_CONFIG {
        string sport
        string seasons
        string model_id
        string calibrator_id
        string sizing_strategy
        float  starting_bankroll
        float  min_edge
        float  kelly_fraction
        int    lookback_games
    }
    BACKTEST_RUN {
        string    id
        string    config_id
        timestamp run_at
        int       lookahead_violations
    }

    BACKTEST_CONFIG ||--o{ BACKTEST_RUN : "executed as"
```

| Entity | Field | Note |
|--------|-------|------|
| BACKTEST_CONFIG | seasons | List of season identifiers to replay, e.g. `["2021", "2022", "2023"]` |
| BACKTEST_CONFIG | min_edge | Minimum edge threshold passed to the `ValueDetector`; e.g. `0.03` for 3% |
| BACKTEST_CONFIG | lookback_games | How many games of history the model uses for its training window |
| BACKTEST_RUN | lookahead_violations | Count of future-data access attempts caught by the bias guard; **must be 0 for the run to be valid** |

A `BACKTEST_RUN` produces `BET` records (mode = `backtest`) and a `PERFORMANCE_REPORT` in the Bet Tracking context. Those are the outputs; the backtesting context itself holds only the configuration and run metadata.

---

## Cross-Context Data Flow

```
[Market Data]
  EVENT, MARKET, LINE
        │
        │ line_id reference
        ▼
[Value Analysis] ◄── calibrated_estimate_id ── [Calibration] ◄── [Statistical Modeling]
        │
        │ value_bet_id reference
        ▼
[Bet Tracking]
  BET, BET_RESULT, PERFORMANCE_REPORT
        ▲
        │ bet_id reference
[Value Analysis]
  CLV_RECORD (resolved after game using closing LINE from Market Data)
```

No context holds a full entity from another context. Every cross-context link is a reference by ID. This is what allows each context to evolve its internal model independently and what makes the `OddsProvider` and `BookmakerClient` substitution possible without touching any upstream logic.
