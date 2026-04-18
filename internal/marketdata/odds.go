package marketdata

import (
	"errors"
	"fmt"
)

// ErrInvalidOdds is returned when an odds value cannot be converted.
var ErrInvalidOdds = errors.New("invalid odds")

// AmericanOdds represents a moneyline price in American format (e.g., -110, +150).
// Positive values indicate the profit on a $100 stake.
// Negative values indicate the stake required to profit $100.
type AmericanOdds int

// DecimalOdds represents a price as a decimal multiplier (e.g., 1.909, 2.50).
// Total return including the original stake = stake × decimal.
type DecimalOdds float64

// FractionalOdds represents a price as a fraction (e.g., 10/11, 3/2).
type FractionalOdds struct {
	Numerator   int
	Denominator int
}

// ImpliedProbability is a probability in (0, 1) derived from an odds price.
type ImpliedProbability float64

// ToDecimal converts American odds to decimal odds.
// Returns ErrInvalidOdds if the value is zero.
func (a AmericanOdds) ToDecimal() (DecimalOdds, error) {
	if a == 0 {
		return 0, fmt.Errorf("%w: american odds cannot be zero", ErrInvalidOdds)
	}
	if a > 0 {
		return DecimalOdds(float64(a)/100.0 + 1.0), nil
	}
	return DecimalOdds(100.0/float64(-a) + 1.0), nil
}

// ToImpliedProbability converts decimal odds to an implied probability.
// Returns ErrInvalidOdds if the decimal is not greater than 1.
func (d DecimalOdds) ToImpliedProbability() (ImpliedProbability, error) {
	if d <= 1.0 {
		return 0, fmt.Errorf("%w: decimal odds must be greater than 1, got %f", ErrInvalidOdds, d)
	}
	return ImpliedProbability(1.0 / float64(d)), nil
}

// ToDecimal converts fractional odds to decimal odds.
// Returns ErrInvalidOdds if the denominator is zero.
func (f FractionalOdds) ToDecimal() (DecimalOdds, error) {
	if f.Denominator == 0 {
		return 0, fmt.Errorf("%w: fractional denominator cannot be zero", ErrInvalidOdds)
	}
	return DecimalOdds(float64(f.Numerator)/float64(f.Denominator) + 1.0), nil
}

// ToDecimal converts an implied probability back to decimal odds.
// Returns ErrInvalidOdds if the probability is not strictly in (0, 1).
func (p ImpliedProbability) ToDecimal() (DecimalOdds, error) {
	if p <= 0 || p >= 1 {
		return 0, fmt.Errorf("%w: implied probability must be in (0, 1), got %f", ErrInvalidOdds, p)
	}
	return DecimalOdds(1.0 / float64(p)), nil
}
