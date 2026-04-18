package sizing

import "math"

// FullKelly returns f* = max(0, edge / (decimalOdds − 1)).
//
// Returns 0 when edge ≤ 0 or decimalOdds ≤ 1.
func FullKelly(edge, decimalOdds float64) float64 {
	if decimalOdds <= 1.0 {
		return 0.0
	}
	return math.Max(0.0, edge/(decimalOdds-1.0))
}

// ComputeKellyFraction returns all three Kelly variants for the given edge and odds.
func ComputeKellyFraction(edge, decimalOdds float64) KellyFraction {
	f := FullKelly(edge, decimalOdds)
	return KellyFraction{
		Full:    f,
		Half:    f / 2.0,
		Quarter: f / 4.0,
	}
}

// KellySizer sizes bets using a configurable fraction of the Kelly Criterion.
type KellySizer struct {
	// Fraction is the multiplier applied to full Kelly.
	// 1.0 = full Kelly, 0.5 = half Kelly, 0.25 = quarter Kelly.
	Fraction float64
}

// Size computes the Kelly-derived stake.
func (s KellySizer) Size(edge, decimalOdds, bankroll float64) BetSizing {
	f := FullKelly(edge, decimalOdds) * s.Fraction
	return BetSizing{
		Stake:    bankroll * f,
		Fraction: f,
		Bankroll: bankroll,
	}
}
