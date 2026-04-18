package marketdata_test

import (
	"context"
	"math"
	"path/filepath"
	"testing"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

func TestNewStaticOddsProviderMissingFile(t *testing.T) {
	_, err := marketdata.NewStaticOddsProvider("nonexistent.json")
	if err == nil {
		t.Error("expected error for missing file, got nil")
	}
}

func TestStaticOddsProvider(t *testing.T) {
	ctx := context.Background()
	p, err := marketdata.NewStaticOddsProvider(filepath.Join("testdata", "sample_odds.json"))
	if err != nil {
		t.Fatalf("NewStaticOddsProvider: %v", err)
	}

	t.Run("returns events for matching sport and season", func(t *testing.T) {
		events, err := p.Events(ctx, marketdata.SportNFL, "2023")
		if err != nil {
			t.Fatalf("Events: %v", err)
		}
		if len(events) != 1 {
			t.Errorf("Events() count = %d, want 1", len(events))
		}
		if events[0].ID != "nfl-2023-week1-kc-chi" {
			t.Errorf("Events()[0].ID = %q, want %q", events[0].ID, "nfl-2023-week1-kc-chi")
		}
	})

	t.Run("returns empty for unknown season", func(t *testing.T) {
		events, err := p.Events(ctx, marketdata.SportNFL, "9999")
		if err != nil {
			t.Fatalf("Events: %v", err)
		}
		if len(events) != 0 {
			t.Errorf("Events() count = %d, want 0", len(events))
		}
	})

	t.Run("returns empty for wrong sport", func(t *testing.T) {
		events, err := p.Events(ctx, marketdata.SportNBA, "2023")
		if err != nil {
			t.Fatalf("Events: %v", err)
		}
		if len(events) != 0 {
			t.Errorf("Events() count = %d, want 0", len(events))
		}
	})

	t.Run("returns markets for event", func(t *testing.T) {
		markets, err := p.Markets(ctx, "nfl-2023-week1-kc-chi")
		if err != nil {
			t.Fatalf("Markets: %v", err)
		}
		if len(markets) != 1 {
			t.Errorf("Markets() count = %d, want 1", len(markets))
		}
		if markets[0].ID != "nfl-2023-week1-kc-chi-ml" {
			t.Errorf("Markets()[0].ID = %q, want %q", markets[0].ID, "nfl-2023-week1-kc-chi-ml")
		}
	})

	t.Run("returns lines with computed decimal odds", func(t *testing.T) {
		lines, err := p.Lines(ctx, "nfl-2023-week1-kc-chi-ml")
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		if len(lines) != 2 {
			t.Errorf("Lines() count = %d, want 2", len(lines))
		}
		for _, l := range lines {
			if l.DecimalOdds == 0 {
				t.Errorf("line %q: DecimalOdds not computed", l.ID)
			}
			if l.RawImpliedProb == 0 {
				t.Errorf("line %q: RawImpliedProb not computed", l.ID)
			}
			if l.ImpliedProb == 0 {
				t.Errorf("line %q: ImpliedProb not devigged", l.ID)
			}
		}
	})

	t.Run("devigged probabilities sum to 1.0", func(t *testing.T) {
		lines, err := p.Lines(ctx, "nfl-2023-week1-kc-chi-ml")
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		var sum float64
		for _, l := range lines {
			sum += l.ImpliedProb
		}
		if math.Abs(sum-1.0) > 1e-9 {
			t.Errorf("ImpliedProb sum = %v, want 1.0", sum)
		}
	})

	t.Run("KC -200 devigged probability is 9/14", func(t *testing.T) {
		lines, err := p.Lines(ctx, "nfl-2023-week1-kc-chi-ml")
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		var homeProb float64
		for _, l := range lines {
			if l.Side == marketdata.SideHome {
				homeProb = l.ImpliedProb
			}
		}
		wantKC := 9.0 / 14.0
		if math.Abs(homeProb-wantKC) > 1e-9 {
			t.Errorf("home ImpliedProb = %v, want %v (9/14)", homeProb, wantKC)
		}
	})
}
