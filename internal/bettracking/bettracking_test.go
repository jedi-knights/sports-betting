package bettracking_test

import (
	"context"
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
// Each subtest arranges its own data with unique IDs so subtests are independent
// and can run in any order without state leaking between them.
func runStoreTests(t *testing.T, store bettracking.BetStore) {
	t.Helper()
	ctx := context.Background()

	t.Run("save and find all", func(t *testing.T) {
		// Arrange
		bet := newBet("b-save-find")

		// Act
		if err := store.Save(ctx, bet); err != nil {
			t.Fatalf("Save: %v", err)
		}
		all, err := store.FindAll(ctx)

		// Assert
		if err != nil {
			t.Fatalf("FindAll: %v", err)
		}
		found := false
		for _, b := range all {
			if b.ID == "b-save-find" {
				found = true
				break
			}
		}
		if !found {
			t.Error("saved bet not found in FindAll")
		}
	})

	t.Run("find by id", func(t *testing.T) {
		// Arrange
		if err := store.Save(ctx, newBet("b-find-id")); err != nil {
			t.Fatalf("Save: %v", err)
		}

		// Act
		bet, err := store.FindByID(ctx, "b-find-id")

		// Assert
		if err != nil {
			t.Fatalf("FindByID: %v", err)
		}
		if bet.ID != "b-find-id" {
			t.Errorf("ID = %s, want b-find-id", bet.ID)
		}
	})

	t.Run("find by id not found", func(t *testing.T) {
		// Arrange / Act
		_, err := store.FindByID(ctx, "completely-absent-id")

		// Assert
		if !errors.Is(err, bettracking.ErrNotFound) {
			t.Errorf("err = %v, want ErrNotFound", err)
		}
	})

	t.Run("duplicate id returns error", func(t *testing.T) {
		// Arrange
		if err := store.Save(ctx, newBet("b-dup")); err != nil {
			t.Fatalf("first Save: %v", err)
		}

		// Act
		err := store.Save(ctx, newBet("b-dup"))

		// Assert
		if !errors.Is(err, bettracking.ErrDuplicateID) {
			t.Errorf("err = %v, want ErrDuplicateID", err)
		}
	})

	t.Run("find by status open", func(t *testing.T) {
		// Arrange
		if err := store.Save(ctx, newBet("b-status-open")); err != nil {
			t.Fatalf("Save: %v", err)
		}

		// Act
		bets, err := store.FindByStatus(ctx, bettracking.BetStatusOpen)

		// Assert
		if err != nil {
			t.Fatalf("FindByStatus: %v", err)
		}
		found := false
		for _, b := range bets {
			if b.ID == "b-status-open" {
				found = true
				break
			}
		}
		if !found {
			t.Error("expected b-status-open in open bets")
		}
	})

	t.Run("update changes status", func(t *testing.T) {
		// Arrange
		if err := store.Save(ctx, newBet("b-update")); err != nil {
			t.Fatalf("Save: %v", err)
		}
		bet, _ := store.FindByID(ctx, "b-update")
		bet.Status = bettracking.BetStatusWon

		// Act
		if err := store.Update(ctx, bet); err != nil {
			t.Fatalf("Update: %v", err)
		}

		// Assert
		updated, _ := store.FindByID(ctx, "b-update")
		if updated.Status != bettracking.BetStatusWon {
			t.Errorf("Status = %s, want won", updated.Status)
		}
	})

	t.Run("update missing id returns error", func(t *testing.T) {
		// Arrange / Act
		err := store.Update(ctx, newBet("nonexistent"))

		// Assert
		if !errors.Is(err, bettracking.ErrNotFound) {
			t.Errorf("err = %v, want ErrNotFound", err)
		}
	})

	t.Run("resolve marks bet won", func(t *testing.T) {
		// Arrange
		if err := store.Save(ctx, newBet("b-resolve-won")); err != nil {
			t.Fatalf("Save: %v", err)
		}

		// Act
		if err := store.Resolve(ctx, "b-resolve-won", true); err != nil {
			t.Fatalf("Resolve: %v", err)
		}

		// Assert
		bet, _ := store.FindByID(ctx, "b-resolve-won")
		if bet.Status != bettracking.BetStatusWon {
			t.Errorf("Status = %s, want won", bet.Status)
		}
	})

	t.Run("resolve marks bet lost", func(t *testing.T) {
		// Arrange
		if err := store.Save(ctx, newBet("b-resolve-lost")); err != nil {
			t.Fatalf("Save: %v", err)
		}

		// Act
		if err := store.Resolve(ctx, "b-resolve-lost", false); err != nil {
			t.Fatalf("Resolve: %v", err)
		}

		// Assert
		bet, _ := store.FindByID(ctx, "b-resolve-lost")
		if bet.Status != bettracking.BetStatusLost {
			t.Errorf("Status = %s, want lost", bet.Status)
		}
	})

	t.Run("find by event id returns matching bets", func(t *testing.T) {
		// Arrange — newBet always uses EventID "event-1"
		if err := store.Save(ctx, newBet("b-event-id")); err != nil {
			t.Fatalf("Save: %v", err)
		}

		// Act
		bets, err := store.FindByEventID(ctx, "event-1")

		// Assert
		if err != nil {
			t.Fatalf("FindByEventID: %v", err)
		}
		found := false
		for _, b := range bets {
			if b.EventID != "event-1" {
				t.Errorf("got EventID %q, want event-1", b.EventID)
			}
			if b.ID == "b-event-id" {
				found = true
			}
		}
		if !found {
			t.Error("expected b-event-id in event-1 results")
		}
	})

	t.Run("find by event id unknown returns empty", func(t *testing.T) {
		// Arrange / Act
		bets, err := store.FindByEventID(ctx, "no-such-event")

		// Assert
		if err != nil {
			t.Fatalf("FindByEventID: %v", err)
		}
		if len(bets) != 0 {
			t.Fatalf("got %d bets, want 0", len(bets))
		}
	})

	t.Run("resolve clv sets closing line value", func(t *testing.T) {
		// Arrange
		if err := store.Save(ctx, newBet("b-clv")); err != nil {
			t.Fatalf("Save: %v", err)
		}

		// Act — bet odds = 2.10, closing odds = 2.0; CLV = 1/2.0 - 1/2.10 ≈ 0.02381
		if err := store.ResolveCLV(ctx, "b-clv", 2.0); err != nil {
			t.Fatalf("ResolveCLV: %v", err)
		}

		// Assert
		bet, _ := store.FindByID(ctx, "b-clv")
		if bet.CLV == nil {
			t.Fatal("CLV is nil after ResolveCLV")
		}
		wantCLV := 1.0/2.0 - 1.0/2.10
		if math.Abs(*bet.CLV-wantCLV) > 1e-9 {
			t.Errorf("CLV = %v, want %v", *bet.CLV, wantCLV)
		}
	})

	t.Run("resolve clv rejects zero closing odds", func(t *testing.T) {
		// Arrange
		if err := store.Save(ctx, newBet("b-clv-zero")); err != nil {
			t.Fatalf("Save: %v", err)
		}

		// Act
		err := store.ResolveCLV(ctx, "b-clv-zero", 0.0)

		// Assert
		if err == nil {
			t.Fatal("expected error for zero closing odds, got nil")
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
		// Arrange
		bet := newBet("x")
		bet.Status = bettracking.BetStatusWon

		// Act
		r := bettracking.NewBetResult(bet)

		// Assert
		want := bet.Stake * (bet.DecimalOdds - 1.0)
		if math.Abs(r.PnL-want) > 1e-9 {
			t.Errorf("PnL = %v, want %v", r.PnL, want)
		}
		if !r.Won {
			t.Error("Won should be true")
		}
	})

	t.Run("lost bet has negative pnl", func(t *testing.T) {
		// Arrange
		bet := newBet("x")
		bet.Status = bettracking.BetStatusLost

		// Act
		r := bettracking.NewBetResult(bet)

		// Assert
		if math.Abs(r.PnL-(-bet.Stake)) > 1e-9 {
			t.Errorf("PnL = %v, want %v", r.PnL, -bet.Stake)
		}
		if r.Won {
			t.Error("Won should be false")
		}
	})

	t.Run("voided bet has zero pnl", func(t *testing.T) {
		// Arrange
		bet := newBet("x")
		bet.Status = bettracking.BetStatusVoided

		// Act
		r := bettracking.NewBetResult(bet)

		// Assert
		if r.PnL != 0.0 {
			t.Errorf("PnL = %v, want 0", r.PnL)
		}
	})

	t.Run("clv propagated from bet", func(t *testing.T) {
		// Arrange
		bet := newBet("x")
		bet.Status = bettracking.BetStatusWon
		clv := 0.025
		bet.CLV = &clv

		// Act
		r := bettracking.NewBetResult(bet)

		// Assert
		if math.Abs(r.CLV-0.025) > 1e-9 {
			t.Errorf("CLV = %v, want 0.025", r.CLV)
		}
	})

	t.Run("nil clv results in zero", func(t *testing.T) {
		// Arrange
		bet := newBet("x")

		// Act
		r := bettracking.NewBetResult(bet)

		// Assert
		if r.CLV != 0.0 {
			t.Errorf("CLV = %v, want 0", r.CLV)
		}
	})
}
