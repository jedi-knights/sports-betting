package bettracking_test

import (
	"errors"
	"math"
	"path/filepath"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/bettracking"
)

var testTime = time.Date(2023, 10, 1, 12, 0, 0, 0, time.UTC)

func newBet(id string) bettracking.Bet {
	return bettracking.Bet{
		ID:          id,
		EventID:     "event-1",
		MarketID:    "market-1",
		Side:        "home_win",
		Stake:       100.0,
		DecimalOdds: 2.10,
		ModelProb:   0.55,
		Edge:        0.155,
		PlacedAt:    testTime,
		Status:      bettracking.BetStatusOpen,
	}
}

// runStoreTests runs the same behavioural tests against any BetStore implementation.
func runStoreTests(t *testing.T, store bettracking.BetStore) {
	t.Helper()

	t.Run("save and find all", func(t *testing.T) {
		bet := newBet("b1")
		if err := store.Save(bet); err != nil {
			t.Fatalf("Save: %v", err)
		}
		all, err := store.FindAll()
		if err != nil {
			t.Fatalf("FindAll: %v", err)
		}
		if len(all) != 1 {
			t.Fatalf("FindAll len = %d, want 1", len(all))
		}
		if all[0].ID != "b1" {
			t.Errorf("ID = %s, want b1", all[0].ID)
		}
	})

	t.Run("find by id", func(t *testing.T) {
		bet, err := store.FindByID("b1")
		if err != nil {
			t.Fatalf("FindByID: %v", err)
		}
		if bet.ID != "b1" {
			t.Errorf("ID = %s, want b1", bet.ID)
		}
	})

	t.Run("find by id not found", func(t *testing.T) {
		_, err := store.FindByID("missing")
		if !errors.Is(err, bettracking.ErrNotFound) {
			t.Errorf("err = %v, want ErrNotFound", err)
		}
	})

	t.Run("duplicate id returns error", func(t *testing.T) {
		err := store.Save(newBet("b1"))
		if !errors.Is(err, bettracking.ErrDuplicateID) {
			t.Errorf("err = %v, want ErrDuplicateID", err)
		}
	})

	t.Run("find by status open", func(t *testing.T) {
		bets, err := store.FindByStatus(bettracking.BetStatusOpen)
		if err != nil {
			t.Fatalf("FindByStatus: %v", err)
		}
		if len(bets) == 0 {
			t.Error("expected at least one open bet")
		}
	})

	t.Run("update changes status", func(t *testing.T) {
		bet, _ := store.FindByID("b1")
		bet.Status = bettracking.BetStatusWon
		if err := store.Update(bet); err != nil {
			t.Fatalf("Update: %v", err)
		}
		updated, _ := store.FindByID("b1")
		if updated.Status != bettracking.BetStatusWon {
			t.Errorf("Status = %s, want won", updated.Status)
		}
	})

	t.Run("update missing id returns error", func(t *testing.T) {
		err := store.Update(newBet("nonexistent"))
		if !errors.Is(err, bettracking.ErrNotFound) {
			t.Errorf("err = %v, want ErrNotFound", err)
		}
	})

	t.Run("resolve marks bet won", func(t *testing.T) {
		if err := store.Save(newBet("b2")); err != nil {
			t.Fatalf("Save: %v", err)
		}
		if err := store.Resolve("b2", true); err != nil {
			t.Fatalf("Resolve: %v", err)
		}
		bet, _ := store.FindByID("b2")
		if bet.Status != bettracking.BetStatusWon {
			t.Errorf("Status = %s, want won", bet.Status)
		}
	})

	t.Run("resolve marks bet lost", func(t *testing.T) {
		if err := store.Save(newBet("b3")); err != nil {
			t.Fatalf("Save: %v", err)
		}
		if err := store.Resolve("b3", false); err != nil {
			t.Fatalf("Resolve: %v", err)
		}
		bet, _ := store.FindByID("b3")
		if bet.Status != bettracking.BetStatusLost {
			t.Errorf("Status = %s, want lost", bet.Status)
		}
	})

	t.Run("resolve clv sets closing line value", func(t *testing.T) {
		if err := store.Save(newBet("b4")); err != nil {
			t.Fatalf("Save: %v", err)
		}
		// bet odds = 2.10, closing odds = 2.0
		// CLV = 1/2.0 - 1/2.10 ≈ 0.02381
		if err := store.ResolveCLV("b4", 2.0); err != nil {
			t.Fatalf("ResolveCLV: %v", err)
		}
		bet, _ := store.FindByID("b4")
		if bet.CLV == nil {
			t.Fatal("CLV is nil after ResolveCLV")
		}
		wantCLV := 1.0/2.0 - 1.0/2.10
		if math.Abs(*bet.CLV-wantCLV) > 1e-9 {
			t.Errorf("CLV = %v, want %v", *bet.CLV, wantCLV)
		}
	})
}

func TestMemoryBetStore(t *testing.T) {
	runStoreTests(t, bettracking.NewMemoryBetStore())
}

func TestCSVBetStore(t *testing.T) {
	path := filepath.Join(t.TempDir(), "bets.csv")
	store, err := bettracking.NewCSVBetStore(path)
	if err != nil {
		t.Fatalf("NewCSVBetStore: %v", err)
	}
	runStoreTests(t, store)
}

func TestNewBetResult(t *testing.T) {
	t.Run("won bet has positive pnl", func(t *testing.T) {
		bet := newBet("x")
		bet.Status = bettracking.BetStatusWon
		r := bettracking.NewBetResult(bet)
		want := bet.Stake * (bet.DecimalOdds - 1.0)
		if math.Abs(r.PnL-want) > 1e-9 {
			t.Errorf("PnL = %v, want %v", r.PnL, want)
		}
		if !r.Won {
			t.Error("Won should be true")
		}
	})

	t.Run("lost bet has negative pnl", func(t *testing.T) {
		bet := newBet("x")
		bet.Status = bettracking.BetStatusLost
		r := bettracking.NewBetResult(bet)
		if math.Abs(r.PnL-(-bet.Stake)) > 1e-9 {
			t.Errorf("PnL = %v, want %v", r.PnL, -bet.Stake)
		}
		if r.Won {
			t.Error("Won should be false")
		}
	})

	t.Run("voided bet has zero pnl", func(t *testing.T) {
		bet := newBet("x")
		bet.Status = bettracking.BetStatusVoided
		r := bettracking.NewBetResult(bet)
		if r.PnL != 0.0 {
			t.Errorf("PnL = %v, want 0", r.PnL)
		}
	})

	t.Run("clv propagated from bet", func(t *testing.T) {
		bet := newBet("x")
		bet.Status = bettracking.BetStatusWon
		clv := 0.025
		bet.CLV = &clv
		r := bettracking.NewBetResult(bet)
		if math.Abs(r.CLV-0.025) > 1e-9 {
			t.Errorf("CLV = %v, want 0.025", r.CLV)
		}
	})

	t.Run("nil clv results in zero", func(t *testing.T) {
		bet := newBet("x")
		r := bettracking.NewBetResult(bet)
		if r.CLV != 0.0 {
			t.Errorf("CLV = %v, want 0", r.CLV)
		}
	})
}
