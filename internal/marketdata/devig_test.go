package marketdata_test

import (
	"math"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

func TestDevig(t *testing.T) {
	t.Run("nil input returns nil", func(t *testing.T) {
		if got := marketdata.Devig(nil); got != nil {
			t.Errorf("Devig(nil) = %v, want nil", got)
		}
	})

	t.Run("empty input returns nil", func(t *testing.T) {
		if got := marketdata.Devig([]float64{}); got != nil {
			t.Errorf("Devig([]) = %v, want nil", got)
		}
	})

	t.Run("two equal sides sum to 1.0 with each at 0.5", func(t *testing.T) {
		// -110 / -110 market: each raw prob = 100/210
		raw := 100.0 / 210.0
		got := marketdata.Devig([]float64{raw, raw})

		if math.Abs(got[0]+got[1]-1.0) > 1e-9 {
			t.Errorf("sum = %v, want 1.0", got[0]+got[1])
		}
		if math.Abs(got[0]-0.5) > 1e-9 {
			t.Errorf("got[0] = %v, want 0.5", got[0])
		}
	})

	t.Run("three-sided market sums to 1.0", func(t *testing.T) {
		got := marketdata.Devig([]float64{0.40, 0.35, 0.30}) // sum = 1.05
		sum := got[0] + got[1] + got[2]
		if math.Abs(sum-1.0) > 1e-9 {
			t.Errorf("sum = %v, want 1.0", sum)
		}
	})

	t.Run("preserves relative proportions (KC -200 vs CHI +170)", func(t *testing.T) {
		// KC -200: decimal = 1.5, raw = 1/1.5 = 2/3
		// CHI +170: decimal = 2.7, raw = 1/2.7 = 10/27
		rawKC := 2.0 / 3.0
		rawCHI := 10.0 / 27.0
		got := marketdata.Devig([]float64{rawKC, rawCHI})

		// Exact: sum = 2/3 + 10/27 = 18/27 + 10/27 = 28/27
		// KC devigged = (2/3) / (28/27) = (2/3)*(27/28) = 9/14
		// CHI devigged = (10/27) / (28/27) = 10/28 = 5/14
		wantKC := 9.0 / 14.0
		wantCHI := 5.0 / 14.0
		if math.Abs(got[0]-wantKC) > 1e-9 {
			t.Errorf("KC = %v, want %v", got[0], wantKC)
		}
		if math.Abs(got[1]-wantCHI) > 1e-9 {
			t.Errorf("CHI = %v, want %v", got[1], wantCHI)
		}
	})

	t.Run("all-zero input returns nil", func(t *testing.T) {
		// Arrange
		input := []float64{0, 0}

		// Act
		got := marketdata.Devig(input)

		// Assert
		if got != nil {
			t.Errorf("Devig(zeros) = %v, want nil", got)
		}
	})

	t.Run("negative input returns nil", func(t *testing.T) {
		// Arrange
		input := []float64{-0.5, 0.5}

		// Act
		got := marketdata.Devig(input)

		// Assert
		if got != nil {
			t.Errorf("Devig(negative) = %v, want nil", got)
		}
	})
}

func TestDevigLines(t *testing.T) {
	now := time.Date(2023, 9, 7, 10, 0, 0, 0, time.UTC)

	lines := []marketdata.Line{
		{
			ID:             "home",
			MarketID:       "m1",
			BookID:         "pinnacle",
			Side:           marketdata.SideHome,
			AmericanOdds:   -200,
			RawImpliedProb: 2.0 / 3.0,
			RecordedAt:     now,
		},
		{
			ID:             "away",
			MarketID:       "m1",
			BookID:         "pinnacle",
			Side:           marketdata.SideAway,
			AmericanOdds:   170,
			RawImpliedProb: 10.0 / 27.0,
			RecordedAt:     now,
		},
	}

	got := marketdata.DevigLines(lines)

	sum := got[0].ImpliedProb + got[1].ImpliedProb
	if math.Abs(sum-1.0) > 1e-9 {
		t.Errorf("ImpliedProb sum = %v, want 1.0", sum)
	}

	wantHome := 9.0 / 14.0
	if math.Abs(got[0].ImpliedProb-wantHome) > 1e-9 {
		t.Errorf("home ImpliedProb = %v, want %v", got[0].ImpliedProb, wantHome)
	}

	// DevigLines must not mutate the original slice
	if lines[0].ImpliedProb != 0 {
		t.Error("DevigLines mutated the original lines slice")
	}
}

func TestDevigLinesIsolatesSnapshots(t *testing.T) {
	// Two different books on the same market should be devigged independently.
	now := time.Date(2023, 9, 7, 10, 0, 0, 0, time.UTC)
	lines := []marketdata.Line{
		{ID: "p-home", MarketID: "m1", BookID: "pinnacle", Side: marketdata.SideHome, RawImpliedProb: 0.60, RecordedAt: now},
		{ID: "p-away", MarketID: "m1", BookID: "pinnacle", Side: marketdata.SideAway, RawImpliedProb: 0.45, RecordedAt: now},
		{ID: "dk-home", MarketID: "m1", BookID: "draftkings", Side: marketdata.SideHome, RawImpliedProb: 0.58, RecordedAt: now},
		{ID: "dk-away", MarketID: "m1", BookID: "draftkings", Side: marketdata.SideAway, RawImpliedProb: 0.47, RecordedAt: now},
	}
	got := marketdata.DevigLines(lines)

	for i := 0; i < len(got); i += 2 {
		sum := got[i].ImpliedProb + got[i+1].ImpliedProb
		if math.Abs(sum-1.0) > 1e-9 {
			t.Errorf("snapshot %d+%d sum = %v, want 1.0", i, i+1, sum)
		}
	}
}
