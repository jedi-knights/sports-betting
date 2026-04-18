# Data Models

Canonical type definitions for all bounded contexts. These models are the contract between contexts — implementation files must conform to the shapes defined here. Go types are used in services and APIs; Python types are used in the modeling and CLI stack.

Each context owns its types. When two contexts need to share a concept, they pass it across a defined interface — they do not share a type definition. For example, `Value Analysis` receives a `CalibratedProbabilityEstimate` from `Calibration` and a `Line` from `Market Data`; it does not reach into either context's internals.

---

## Market Data Context (Go)

The foundational context. All other contexts consume from this one directly or indirectly.

```go
// Sport identifies the sport being modeled.
type Sport string

const (
    NFL    Sport = "nfl"
    NBA    Sport = "nba"
    MLB    Sport = "mlb"
    NHL    Sport = "nhl"
    Soccer Sport = "soccer"
)

// BookType classifies a bookmaker by its market behavior.
// Sharp books (Pinnacle, Circa) set sharp prices and accept large bets.
// Soft books (DraftKings, FanDuel) limit winning players aggressively.
// Exchanges (Betfair) match bettors against each other.
type BookType string

const (
    SharpBook    BookType = "sharp"
    SoftBook     BookType = "soft"
    Exchange     BookType = "exchange"
)

type Book struct {
    ID      string
    Name    string
    Type    BookType
}

// Event represents a single game or match.
type Event struct {
    ID         string
    Sport      Sport
    HomeTeam   string
    AwayTeam   string
    StartsAt   time.Time
    Season     string
    Week       int    // set for NFL; zero for other sports
    Venue      string
}

// MarketType identifies what is being wagered on.
type MarketType string

const (
    Moneyline  MarketType = "moneyline"
    Spread     MarketType = "spread"
    Total      MarketType = "total"
    PlayerProp MarketType = "player_prop"
)

// OutcomeSide is one side of a two- or three-way market.
type OutcomeSide string

const (
    Home  OutcomeSide = "home"
    Away  OutcomeSide = "away"
    Draw  OutcomeSide = "draw"   // soccer and some NHL markets
    Over  OutcomeSide = "over"
    Under OutcomeSide = "under"
)

// Market is a wagerable question for a specific Event.
// One Event has multiple Markets (moneyline, spread, total, etc.).
type Market struct {
    ID        string
    EventID   string
    Type      MarketType
    CreatedAt time.Time
}

// AmericanOdds is the US standard format. Negative = favorite, positive = underdog.
// -110 means bet 110 to win 100. +150 means bet 100 to win 150.
type AmericanOdds int

// DecimalOdds is the European format. The total payout including stake.
// 1.909 means bet 1 to return 1.909 (profit of 0.909).
type DecimalOdds float64

// ImpliedProbability is a probability in [0, 1] derived from odds.
type ImpliedProbability float64

// Odds holds all representations of the same price, plus the deviggged probability.
// RawImplied includes the bookmaker's margin; Implied has the margin removed.
type Odds struct {
    American   AmericanOdds
    Decimal    DecimalOdds
    RawImplied ImpliedProbability // includes bookmaker margin (overround)
    Implied    ImpliedProbability // devigged — true market probability estimate
}

// Line is a specific bookmaker's price on one side of one market at a point in time.
// Line movement is tracked by storing multiple Line records per market/book/outcome.
type Line struct {
    ID         string
    MarketID   string
    Book       Book
    Side       OutcomeSide
    Label      string     // human label: "Kansas City Chiefs", "Over 47.5", etc.
    Odds       Odds
    Spread     *float64   // set for spread markets; nil otherwise
    Total      *float64   // set for totals markets; nil otherwise
    RecordedAt time.Time
    IsClosing  bool       // true if this is the line recorded at game time
}
```

### Market Data Ports

```go
// OddsProvider is the primary inbound port for market data.
// The static file implementation is used in backtesting.
// A live bookmaker client implements this interface in Phase 9.
type OddsProvider interface {
    GetEvents(ctx context.Context, sport Sport, date time.Time) ([]Event, error)
    GetMarkets(ctx context.Context, eventID string) ([]Market, error)
    GetLines(ctx context.Context, marketID string) ([]Line, error)
    GetClosingLine(ctx context.Context, marketID string, side OutcomeSide) (Line, error)
}

// LineStore is the persistence port for odds history.
type LineStore interface {
    SaveLine(ctx context.Context, line Line) error
    GetLine(ctx context.Context, lineID string) (Line, error)
    GetLinesByMarket(ctx context.Context, marketID string) ([]Line, error)
    GetLatestLine(ctx context.Context, marketID string, bookID string, side OutcomeSide) (Line, error)
}

// BookmakerClient is the future live execution port.
// Until Phase 9, only a mock implementation exists.
// Defined here so all upstream interfaces never depend on it directly.
type BookmakerClient interface {
    GetOdds(ctx context.Context, eventID string) ([]Line, error)
    PlaceBet(ctx context.Context, lineID string, stake float64) (PlacedBet, error)
    GetBalance(ctx context.Context) (float64, error)
    GetOpenBets(ctx context.Context) ([]PlacedBet, error)
}

// PlacedBet is the confirmation returned by a BookmakerClient after bet placement.
type PlacedBet struct {
    ExternalID  string    // bookmaker's own reference number
    LineID      string
    Stake       float64
    DecimalOdds float64
    PlacedAt    time.Time
}
```

---

## Statistical Modeling Context (Python)

All types are Python dataclasses unless otherwise noted. Protocols use `typing.Protocol`.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class FeatureSet:
    """Named numeric features for a single event, computed as of a specific point in time.

    The as_of field is a lookahead guard: no feature may be derived from data
    after this timestamp.
    """
    event_id: str
    sport: str
    home_team: str
    away_team: str
    as_of: datetime
    features: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ProbabilityEstimate:
    """Raw model output: win probabilities for each outcome.

    draw is None for sports that have no draw outcome (NFL, NBA, MLB).
    The three probabilities must sum to 1.0.
    """
    event_id: str
    model_id: str
    generated_at: datetime
    home_win: float
    away_win: float
    draw: float | None = None   # None for sports without draws


@dataclass(frozen=True)
class ActualOutcome:
    """Observed result of a completed event. Used for model training and evaluation."""
    event_id: str
    home_score: int
    away_score: int
    final_at: datetime

    @property
    def home_win(self) -> bool:
        return self.home_score > self.away_score

    @property
    def away_win(self) -> bool:
        return self.away_score > self.home_score

    @property
    def draw(self) -> bool:
        return self.home_score == self.away_score


@dataclass
class TrainingExample:
    features: FeatureSet
    outcome: ActualOutcome


class Model(Protocol):
    """The common contract for all predictive models."""

    @property
    def model_id(self) -> str: ...

    def fit(self, examples: list[TrainingExample]) -> None: ...

    def predict(self, features: FeatureSet) -> ProbabilityEstimate: ...


class FeatureExtractor(Protocol):
    """Computes a FeatureSet for an event from available historical data."""

    def extract(self, event_id: str, as_of: datetime) -> FeatureSet: ...
```

---

## Calibration Context (Python)

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CalibratedProbabilityEstimate:
    """A ProbabilityEstimate after post-hoc calibration has been applied.

    The raw field preserves the original model output for comparison.
    calibrated_* fields are the values to use for EV calculation.
    """
    raw: ProbabilityEstimate
    calibrator_id: str
    calibrated_home_win: float
    calibrated_away_win: float
    calibrated_draw: float | None   # None for sports without draws


@dataclass
class CalibrationCurve:
    """Output of calibration quality evaluation against a holdout set."""
    model_id: str
    calibrator_id: str
    bin_edges: list[float]
    fraction_positive: list[float]  # observed frequency per predicted-probability bin
    mean_predicted: list[float]     # mean predicted probability per bin
    brier_score: float              # lower is better; perfectly calibrated = 0
    log_loss: float                 # lower is better


class Calibrator(Protocol):
    """Post-hoc calibration wrapper. Fit on holdout data; transform at inference time."""

    @property
    def calibrator_id(self) -> str: ...

    def fit(self, probs: list[float], outcomes: list[int]) -> None: ...

    def transform(self, probs: list[float]) -> list[float]: ...
```

---

## Value Analysis Context (Python)

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ValueBet:
    """A bet signal: a market where the model's calibrated probability exceeds
    the market-implied probability by more than the minimum edge threshold.

    ev = (model_prob × decimal_odds) - 1
    edge = model_prob - market_implied_prob (after devig)

    Both must be positive for a bet to be considered a value bet.
    """
    event_id: str
    line_id: str         # the specific bookmaker line being evaluated
    market_type: str
    side: str            # "home", "away", "draw", "over", "under"
    book: str
    model_prob: float
    market_implied_prob: float  # devigged
    decimal_odds: float
    ev: float
    edge: float
    detected_at: datetime


@dataclass
class CLVRecord:
    """Closing Line Value: how the odds at bet time compare to the closing line.

    Positive CLV means the bet was placed at better odds than the market settled at —
    a sign of a well-timed edge regardless of outcome. CLV is the primary long-run
    signal that a model is finding genuine value.

    clv = closing_implied_prob - bet_implied_prob (positive = better than close)
    """
    bet_id: str
    bet_implied_prob: float
    closing_implied_prob: float
    clv: float
    resolved_at: datetime
```

---

## Bankroll Management Context (Python + Go)

These types exist in both languages. The Python version is used in the modeling CLI; the Go version in the service layer.

**Python:**

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Literal


@dataclass
class Bankroll:
    total: float
    available: float    # total minus reserved for open bets
    currency: str = "USD"


SizingStrategy = Literal["full_kelly", "half_kelly", "quarter_kelly", "flat"]


@dataclass(frozen=True)
class BetSizing:
    strategy: SizingStrategy
    stake: float
    fraction: float         # stake / bankroll.total
    kelly_fraction: float   # raw Kelly value before fractional reduction


class Sizer(Protocol):
    """Computes a stake given edge, odds, and current bankroll."""

    def size(
        self,
        ev: float,
        decimal_odds: float,
        bankroll: Bankroll,
    ) -> BetSizing: ...
```

**Go (service layer):**

```go
type SizingStrategy string

const (
    FullKelly     SizingStrategy = "full_kelly"
    HalfKelly     SizingStrategy = "half_kelly"
    QuarterKelly  SizingStrategy = "quarter_kelly"
    FlatUnit      SizingStrategy = "flat"
)

type Bankroll struct {
    Total     float64
    Available float64
    Currency  string
}

type BetSizing struct {
    Strategy      SizingStrategy
    Stake         float64
    Fraction      float64 // stake / total bankroll
    KellyFraction float64 // raw Kelly fraction before scaling
}

// Sizer computes a stake size.
type Sizer interface {
    Size(ev float64, decimalOdds float64, bankroll Bankroll) (BetSizing, error)
}
```

---

## Bet Tracking Context (Go)

```go
// BetStatus tracks the lifecycle of a recorded bet.
type BetStatus string

const (
    BetPending BetStatus = "pending"  // placed, game not yet started
    BetOpen    BetStatus = "open"     // game in progress
    BetWon     BetStatus = "won"
    BetLost    BetStatus = "lost"
    BetVoid    BetStatus = "void"     // game cancelled; stake returned
    BetPaper   BetStatus = "paper"    // simulated; no real money
)

// BetMode distinguishes simulation from live execution.
type BetMode string

const (
    Backtest    BetMode = "backtest"
    PaperTrade  BetMode = "paper"
    Live        BetMode = "live"
)

// Bet is the canonical record of a single wager.
type Bet struct {
    ID            string
    ValueBetID    string      // the ValueBet signal that generated this record
    EventID       string
    MarketType    string
    Side          string
    Book          string
    DecimalOdds   float64
    Stake         float64
    ToWin         float64     // stake × (decimal_odds - 1)
    Status        BetStatus
    Mode          BetMode
    PlacedAt      time.Time
    ResolvedAt    *time.Time  // nil until the game is final
    ExternalID    string      // bookmaker reference number; empty for paper/backtest
    Notes         string
}

// BetResult holds the financial outcome after resolution.
type BetResult struct {
    BetID   string
    Profit  float64     // positive for wins, negative for losses, zero for void
    ROI     float64     // profit / stake
    CLV     *float64    // nil until closing line is resolved
}

// PerformanceReport aggregates results over a time window or full history.
type PerformanceReport struct {
    Period       string
    Mode         BetMode
    TotalBets    int
    WonBets      int
    LostBets     int
    VoidBets     int
    TotalStaked  float64
    TotalProfit  float64
    ROI          float64  // TotalProfit / TotalStaked
    WinRate      float64  // WonBets / (WonBets + LostBets)
    AverageCLV   float64
    MaxDrawdown  float64
    SharpeRatio  float64
}
```

### Bet Tracking Port

```go
// BetStore is the persistence port for all bet records.
type BetStore interface {
    SaveBet(ctx context.Context, bet Bet) error
    UpdateBet(ctx context.Context, bet Bet) error
    GetBet(ctx context.Context, betID string) (Bet, error)
    GetBetsByStatus(ctx context.Context, status BetStatus) ([]Bet, error)
    GetBetsByMode(ctx context.Context, mode BetMode) ([]Bet, error)
    GetPerformanceReport(ctx context.Context, mode BetMode, period string) (PerformanceReport, error)
}
```

---

## Backtesting Context (Python)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BacktestConfig:
    sport: str
    seasons: list[str]         # e.g., ["2021", "2022", "2023"]
    model_id: str
    calibrator_id: str
    sizing_strategy: str       # matches SizingStrategy literals
    starting_bankroll: float
    min_edge: float            # minimum edge threshold for ValueDetector
    kelly_fraction: float      # 1.0 = full, 0.5 = half, 0.25 = quarter
    lookback_games: int        # how many games of history the model uses for training


@dataclass
class BacktestResult:
    config: BacktestConfig
    run_at: datetime
    bets: list[dict]           # serialized Bet records
    report: dict               # serialized PerformanceReport
    calibration_curve: dict    # serialized CalibrationCurve
    lookahead_violations: int  # count of lookahead bias guards triggered; must be 0
```

---

## Type Relationships Across Contexts

```
[Market Data]
  Event, Market, Line, Odds
        │
        ▼ (Line passed to)
[Value Analysis]
        │ also receives ▼
[Statistical Modeling] → ProbabilityEstimate
        │
        ▼ (wrapped by)
[Calibration] → CalibratedProbabilityEstimate
        │
        ▼ (passed to)
[Value Analysis] → ValueBet
        │
        ▼ (passed to)
[Bankroll Management] → BetSizing
        │
        ▼ (combined into)
[Bet Tracking] → Bet → BetResult → PerformanceReport
```

No context imports types from a context below it in this diagram.
`Market Data` has no imports from any other context.
`Statistical Modeling` has no imports from any other context.
`Value Analysis` imports from `Market Data` and `Calibration`.
`Bankroll Management` imports from `Value Analysis` only (receives `ev` and `decimal_odds`).
`Bet Tracking` imports from `Bankroll Management` and `Value Analysis`.
