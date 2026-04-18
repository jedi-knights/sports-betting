package sizing_test

import (
	"math"
	"testing"

	"github.com/jedi-knights/sports-betting/internal/sizing"
)

func TestFullKelly(t *testing.T) {
	tests := []struct {
		name          string
		edge, odds    float64
		want          float64
	}{
		{"positive edge", 0.10, 2.0, 0.10},
		{"high odds", 0.05, 1.5, 0.10},
		{"zero edge", 0.0, 2.0, 0.0},
		{"negative edge", -0.10, 2.0, 0.0},
		{"odds at one", 0.10, 1.0, 0.0},
		{"odds below one", 0.10, 0.5, 0.0},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := sizing.FullKelly(tt.edge, tt.odds)
			if math.Abs(got-tt.want) > 1e-9 {
				t.Errorf("FullKelly(%v, %v) = %v, want %v", tt.edge, tt.odds, got, tt.want)
			}
		})
	}
}

func TestComputeKellyFraction(t *testing.T) {
	kf := sizing.ComputeKellyFraction(0.10, 2.0)
	if math.Abs(kf.Full-0.10) > 1e-9 {
		t.Errorf("Full = %v, want 0.10", kf.Full)
	}
	if math.Abs(kf.Half-kf.Full/2.0) > 1e-9 {
		t.Errorf("Half = %v, want %v", kf.Half, kf.Full/2.0)
	}
	if math.Abs(kf.Quarter-kf.Full/4.0) > 1e-9 {
		t.Errorf("Quarter = %v, want %v", kf.Quarter, kf.Full/4.0)
	}
}

func TestKellySizer(t *testing.T) {
	tests := []struct {
		name             string
		fraction         float64
		edge, odds, bank float64
		wantStake        float64
		wantFraction     float64
	}{
		{"full kelly", 1.0, 0.10, 2.0, 1000.0, 100.0, 0.10},
		{"half kelly", 0.5, 0.10, 2.0, 1000.0, 50.0, 0.05},
		{"quarter kelly", 0.25, 0.10, 2.0, 1000.0, 25.0, 0.025},
		{"zero edge", 1.0, 0.0, 2.0, 1000.0, 0.0, 0.0},
		{"negative edge", 1.0, -0.10, 2.0, 1000.0, 0.0, 0.0},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			s := sizing.KellySizer{Fraction: tt.fraction}
			got := s.Size(tt.edge, tt.odds, tt.bank)
			if math.Abs(got.Stake-tt.wantStake) > 1e-9 {
				t.Errorf("Stake = %v, want %v", got.Stake, tt.wantStake)
			}
			if math.Abs(got.Fraction-tt.wantFraction) > 1e-9 {
				t.Errorf("Fraction = %v, want %v", got.Fraction, tt.wantFraction)
			}
			if got.Bankroll != tt.bank {
				t.Errorf("Bankroll = %v, want %v", got.Bankroll, tt.bank)
			}
		})
	}
}

func TestFlatUnitSizer(t *testing.T) {
	s := sizing.FlatUnitSizer{Unit: 50.0}

	t.Run("stake equals unit", func(t *testing.T) {
		got := s.Size(0.10, 2.0, 1000.0)
		if got.Stake != 50.0 {
			t.Errorf("Stake = %v, want 50.0", got.Stake)
		}
	})
	t.Run("fraction is unit over bankroll", func(t *testing.T) {
		got := s.Size(0.10, 2.0, 1000.0)
		if math.Abs(got.Fraction-0.05) > 1e-9 {
			t.Errorf("Fraction = %v, want 0.05", got.Fraction)
		}
	})
	t.Run("bankroll preserved", func(t *testing.T) {
		got := s.Size(0.10, 2.0, 1000.0)
		if got.Bankroll != 1000.0 {
			t.Errorf("Bankroll = %v, want 1000.0", got.Bankroll)
		}
	})
	t.Run("zero bankroll fraction is zero", func(t *testing.T) {
		got := s.Size(0.10, 2.0, 0.0)
		if got.Fraction != 0.0 {
			t.Errorf("Fraction = %v, want 0.0", got.Fraction)
		}
	})
	t.Run("ignores edge", func(t *testing.T) {
		low := s.Size(0.01, 2.0, 1000.0)
		high := s.Size(0.99, 2.0, 1000.0)
		if low.Stake != high.Stake {
			t.Errorf("Stake should be constant: low=%v high=%v", low.Stake, high.Stake)
		}
	})
}

func TestSizerInterface(t *testing.T) {
	// Verify both sizers satisfy the Sizer interface at compile time.
	var _ sizing.Sizer = sizing.KellySizer{Fraction: 1.0}
	var _ sizing.Sizer = sizing.FlatUnitSizer{Unit: 10.0}
}
