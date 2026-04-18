// Package valueanalysis provides domain types and core calculations for
// identifying and tracking positive expected-value betting opportunities.
package valueanalysis

import "time"

// Side identifies which outcome in a market a line or bet refers to.
type Side string

const (
	SideHomeWin Side = "home_win"
	SideAwayWin Side = "away_win"
	SideDraw    Side = "draw"
)

// EdgeEstimate holds the raw expected-value calculation for one market side.
// It is produced before any minimum-edge filter is applied.
type EdgeEstimate struct {
	EventID     string
	MarketID    string
	Side        Side
	ModelProb   float64 // calibrated model probability for this side
	MarketProb  float64 // deviggged implied probability from offered odds
	DecimalOdds float64 // offered decimal odds
	Edge        float64 // EV = ModelProb × DecimalOdds − 1
}

// ValueBet is an EdgeEstimate that passed the minimum-edge threshold check.
type ValueBet struct {
	EdgeEstimate
	DetectedAt time.Time
}

// CLVResult records how a placed bet compared to the closing line.
type CLVResult struct {
	ValueBet        ValueBet
	ClosingOdds     float64
	ClosingProb     float64 // 1 / ClosingOdds
	CLV             float64 // ClosingProb − (1 / ValueBet.DecimalOdds)
}

// ExpectedValue computes expected value per unit staked.
//
//	ev = modelProb × decimalOdds − 1
//
// Positive ev indicates a value bet. A value of 0.05 means 5 cents expected
// profit per dollar wagered in the long run.
func ExpectedValue(modelProb, decimalOdds float64) float64 {
	return modelProb*decimalOdds - 1.0
}

// ComputeCLV calculates closing line value for a placed bet.
//
//	CLV = closing_implied_probability − bet_implied_probability
//
// Positive CLV means the bet obtained better odds than the closing line —
// the standard evidence of genuine predictive edge.
func ComputeCLV(bet ValueBet, closingDecimalOdds float64) CLVResult {
	closingProb := 1.0 / closingDecimalOdds
	betImpliedProb := 1.0 / bet.DecimalOdds
	return CLVResult{
		ValueBet:    bet,
		ClosingOdds: closingDecimalOdds,
		ClosingProb: closingProb,
		CLV:         closingProb - betImpliedProb,
	}
}
