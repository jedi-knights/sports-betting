// Package bettracking records bet signals, outcomes, and P&L.
package bettracking

import "time"

// BetStatus represents the lifecycle state of a placed bet.
type BetStatus string

const (
	BetStatusOpen   BetStatus = "open"
	BetStatusWon    BetStatus = "won"
	BetStatusLost   BetStatus = "lost"
	BetStatusVoided BetStatus = "voided"
)

// Bet is a single placed bet signal.
type Bet struct {
	ID          string
	EventID     string
	MarketID    string
	Side        string
	Stake       float64
	DecimalOdds float64
	ModelProb   float64
	Edge        float64
	PlacedAt    time.Time
	Status      BetStatus
	CLV         *float64 // nil until resolved against the closing line
}

// BetResult is the computed financial outcome of a settled bet.
type BetResult struct {
	Bet Bet
	Won bool
	// PnL is stake*(decimal_odds-1) if won; -stake if lost; 0 if voided.
	PnL float64
	// CLV is closing line value; 0 if not yet resolved.
	CLV float64
}

// NewBetResult derives a BetResult from the bet's current status.
func NewBetResult(bet Bet) BetResult {
	pnl := 0.0
	switch bet.Status {
	case BetStatusWon:
		pnl = bet.Stake * (bet.DecimalOdds - 1.0)
	case BetStatusLost:
		pnl = -bet.Stake
	}
	clv := 0.0
	if bet.CLV != nil {
		clv = *bet.CLV
	}
	return BetResult{
		Bet: bet,
		Won: bet.Status == BetStatusWon,
		PnL: pnl,
		CLV: clv,
	}
}
