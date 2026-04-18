// Package sizing provides bankroll management and bet sizing primitives.
package sizing

// BetSizing holds the computed stake recommendation for a single bet.
type BetSizing struct {
	// Stake is the absolute amount to wager.
	Stake float64
	// Fraction is the proportion of bankroll staked.
	Fraction float64
	// Bankroll is the bankroll at the time of sizing.
	Bankroll float64
}

// KellyFraction holds all three Kelly variants for a given edge and odds.
type KellyFraction struct {
	// Full is f* = max(0, edge / (decimalOdds − 1)).
	Full float64
	// Half is f*/2.
	Half float64
	// Quarter is f*/4.
	Quarter float64
}

// Sizer computes a recommended stake from edge, odds, and current bankroll.
type Sizer interface {
	Size(edge, decimalOdds, bankroll float64) BetSizing
}
