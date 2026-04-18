package sizing

// FlatUnitSizer sizes every bet at a fixed unit stake regardless of edge or odds.
type FlatUnitSizer struct {
	// Unit is the fixed stake amount per bet.
	Unit float64
}

// Size returns the configured unit stake.
func (s FlatUnitSizer) Size(edge, decimalOdds, bankroll float64) BetSizing {
	fraction := 0.0
	if bankroll > 0.0 {
		fraction = s.Unit / bankroll
	}
	return BetSizing{
		Stake:    s.Unit,
		Fraction: fraction,
		Bankroll: bankroll,
	}
}
