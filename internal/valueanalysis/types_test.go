package valueanalysis_test

import (
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/valueanalysis"
)

func TestExpectedValue(t *testing.T) {
	cases := []struct {
		name      string
		modelProb float64
		decOdds   float64
		check     func(float64) bool
		label     string
	}{
		{"value bet", 0.55, 2.10, func(ev float64) bool { return ev > 0 }, "EV > 0"},
		{"losing bet", 0.40, 2.10, func(ev float64) bool { return ev < 0 }, "EV < 0"},
		{
			"breakeven",
			1.0 / 2.10, 2.10,
			func(ev float64) bool { return ev > -1e-9 && ev < 1e-9 },
			"EV ≈ 0",
		},
		{"even odds at 50pct", 0.50, 2.0, func(ev float64) bool { return ev > -1e-9 && ev < 1e-9 }, "EV ≈ 0"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			ev := valueanalysis.ExpectedValue(tc.modelProb, tc.decOdds)
			if !tc.check(ev) {
				t.Errorf("ExpectedValue(%v, %v) = %v; want %s", tc.modelProb, tc.decOdds, ev, tc.label)
			}
		})
	}
}

func TestComputeCLV(t *testing.T) {
	makeBet := func(decOdds float64) valueanalysis.ValueBet {
		return valueanalysis.ValueBet{
			EdgeEstimate: valueanalysis.EdgeEstimate{
				EventID:     "game-1",
				Side:        valueanalysis.SideHomeWin,
				DecimalOdds: decOdds,
				Edge:        valueanalysis.ExpectedValue(0.55, decOdds),
			},
			DetectedAt: time.Now(),
		}
	}

	t.Run("positive CLV when closing odds shorter", func(t *testing.T) {
		result := valueanalysis.ComputeCLV(makeBet(2.20), 2.05)
		if result.CLV <= 0 {
			t.Errorf("expected CLV > 0, got %v", result.CLV)
		}
	})

	t.Run("negative CLV when closing odds longer", func(t *testing.T) {
		result := valueanalysis.ComputeCLV(makeBet(2.20), 2.35)
		if result.CLV >= 0 {
			t.Errorf("expected CLV < 0, got %v", result.CLV)
		}
	})

	t.Run("zero CLV when odds unchanged", func(t *testing.T) {
		result := valueanalysis.ComputeCLV(makeBet(2.20), 2.20)
		if result.CLV > 1e-9 || result.CLV < -1e-9 {
			t.Errorf("expected CLV ≈ 0, got %v", result.CLV)
		}
	})

	t.Run("closing prob is 1 over closing odds", func(t *testing.T) {
		result := valueanalysis.ComputeCLV(makeBet(2.00), 2.00)
		want := 0.5
		if result.ClosingProb > want+1e-9 || result.ClosingProb < want-1e-9 {
			t.Errorf("ClosingProb = %v; want %v", result.ClosingProb, want)
		}
	})

	t.Run("CLV matches formula", func(t *testing.T) {
		betOdds := 2.20
		closingOdds := 2.05
		result := valueanalysis.ComputeCLV(makeBet(betOdds), closingOdds)
		expected := 1.0/closingOdds - 1.0/betOdds
		diff := result.CLV - expected
		if diff > 1e-9 || diff < -1e-9 {
			t.Errorf("CLV = %v; want %v", result.CLV, expected)
		}
	})
}
