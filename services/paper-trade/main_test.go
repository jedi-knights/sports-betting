package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/bettracking"
	"github.com/jedi-knights/sports-betting/internal/bookmaker"
	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"log/slog"
)

// newTestService returns a paperTradeService backed by in-memory stores so
// tests run without Kafka or a database.
func newTestService(t *testing.T) *paperTradeService {
	t.Helper()
	return &paperTradeService{
		logger:   slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError})),
		betStore: bettracking.NewMemoryBetStore(),
		book: bookmaker.NewSimulatedBookmakerClient(
			bookmaker.WithMargin(marginAdjustment),
			bookmaker.WithMaxStake(100),
			bookmaker.WithOfferTTL(30*time.Second),
		),
	}
}

func saveBet(t *testing.T, store bettracking.BetStore, bet bettracking.Bet) {
	t.Helper()
	if err := store.Save(context.Background(), bet); err != nil {
		t.Fatalf("saving test bet: %v", err)
	}
}

// TestEnvOr confirms that the helper returns the env value when set and the
// fallback when the key is absent or empty.
func TestEnvOr(t *testing.T) {
	t.Run("returns fallback when key is unset", func(t *testing.T) {
		t.Setenv("PAPER_TEST_VAR", "")
		got := envOr("PAPER_TEST_VAR", "default")
		if got != "default" {
			t.Errorf("got %q, want %q", got, "default")
		}
	})

	t.Run("returns env value when key is set", func(t *testing.T) {
		t.Setenv("PAPER_TEST_VAR", "overridden")
		got := envOr("PAPER_TEST_VAR", "default")
		if got != "overridden" {
			t.Errorf("got %q, want %q", got, "overridden")
		}
	})
}

// TestHandleGetBets_Empty asserts the endpoint returns an empty JSON array
// when no bets have been recorded.
func TestHandleGetBets_Empty(t *testing.T) {
	svc := newTestService(t)
	req := httptest.NewRequest(http.MethodGet, "/paper/bets", nil)
	w := httptest.NewRecorder()

	svc.handleGetBets(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}
	if ct := w.Header().Get("Content-Type"); ct != "application/json" {
		t.Errorf("Content-Type = %q, want %q", ct, "application/json")
	}

	var bets []bettracking.Bet
	if err := json.NewDecoder(w.Body).Decode(&bets); err != nil {
		t.Fatalf("decoding response: %v", err)
	}
	if len(bets) != 0 {
		t.Errorf("got %d bets, want 0", len(bets))
	}
}

// TestHandleGetBets_WithBets asserts the endpoint returns all saved bets.
func TestHandleGetBets_WithBets(t *testing.T) {
	svc := newTestService(t)
	saveBet(t, svc.betStore, bettracking.Bet{
		ID: "b1", EventID: "e1", MarketID: "m1",
		Side: "home_win", Stake: 10.0, DecimalOdds: 2.0,
		PlacedAt: time.Now(), Status: bettracking.BetStatusOpen,
	})
	saveBet(t, svc.betStore, bettracking.Bet{
		ID: "b2", EventID: "e2", MarketID: "m2",
		Side: "away_win", Stake: 5.0, DecimalOdds: 1.8,
		PlacedAt: time.Now(), Status: bettracking.BetStatusOpen,
	})

	req := httptest.NewRequest(http.MethodGet, "/paper/bets", nil)
	w := httptest.NewRecorder()
	svc.handleGetBets(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}
	var bets []bettracking.Bet
	if err := json.NewDecoder(w.Body).Decode(&bets); err != nil {
		t.Fatalf("decoding response: %v", err)
	}
	if len(bets) != 2 {
		t.Errorf("got %d bets, want 2", len(bets))
	}
}

// TestHandleGetPerformance_Empty asserts the endpoint returns a zero-valued
// performance report when no bets have been placed.
func TestHandleGetPerformance_Empty(t *testing.T) {
	svc := newTestService(t)
	req := httptest.NewRequest(http.MethodGet, "/paper/performance", nil)
	w := httptest.NewRecorder()

	svc.handleGetPerformance(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}
	var report map[string]any
	if err := json.NewDecoder(w.Body).Decode(&report); err != nil {
		t.Fatalf("decoding response: %v", err)
	}
	// An empty store produces a report with 0 total bets.
	if report["total_bets"] != float64(0) {
		t.Errorf("total_bets = %v, want 0", report["total_bets"])
	}
}

// TestHandleGameCompleted_ResolvesOpenBets asserts that open bets for the
// completed event are marked won or lost according to the winning side.
func TestHandleGameCompleted_ResolvesOpenBets(t *testing.T) {
	svc := newTestService(t)
	// Sides must match what WinningSide() returns: "home" or "away".
	saveBet(t, svc.betStore, bettracking.Bet{
		ID: "b1", EventID: "game-1", MarketID: "m1",
		Side: "home", Stake: 10.0, DecimalOdds: 2.0,
		PlacedAt: time.Now(), Status: bettracking.BetStatusOpen,
	})
	saveBet(t, svc.betStore, bettracking.Bet{
		ID: "b2", EventID: "game-1", MarketID: "m1",
		Side: "away", Stake: 10.0, DecimalOdds: 2.0,
		PlacedAt: time.Now(), Status: bettracking.BetStatusOpen,
	})

	event := marketdata.GameCompletedEvent{
		Result: marketdata.GameResult{
			EventID:   "game-1",
			HomeScore: 28,
			AwayScore: 14,
		},
	}
	if err := svc.handleGameCompleted(context.Background(), event); err != nil {
		t.Fatalf("handleGameCompleted: %v", err)
	}

	bets, err := svc.betStore.FindByEventID(context.Background(), "game-1")
	if err != nil {
		t.Fatalf("finding bets: %v", err)
	}

	for _, b := range bets {
		if b.Status == bettracking.BetStatusOpen {
			t.Errorf("bet %q still open after resolution", b.ID)
		}
		if b.Side == "home" && b.Status != bettracking.BetStatusWon {
			t.Errorf("bet %q (home) should be BetStatusWon, got %q", b.ID, b.Status)
		}
		if b.Side == "away" && b.Status != bettracking.BetStatusLost {
			t.Errorf("bet %q (away) should be BetStatusLost, got %q", b.ID, b.Status)
		}
	}
}

// TestHandleGameCompleted_IgnoresSettledBets asserts that bets already
// resolved are not processed a second time.
func TestHandleGameCompleted_IgnoresSettledBets(t *testing.T) {
	svc := newTestService(t)
	saveBet(t, svc.betStore, bettracking.Bet{
		ID: "b1", EventID: "game-1", MarketID: "m1",
		Side: "home", Stake: 10.0, DecimalOdds: 2.0,
		PlacedAt: time.Now(), Status: bettracking.BetStatusWon,
	})

	event := marketdata.GameCompletedEvent{
		Result: marketdata.GameResult{
			EventID:   "game-1",
			HomeScore: 28,
			AwayScore: 14,
		},
	}
	// Should not error, and the already-settled bet should remain settled.
	if err := svc.handleGameCompleted(context.Background(), event); err != nil {
		t.Fatalf("handleGameCompleted: %v", err)
	}

	bets, err := svc.betStore.FindByEventID(context.Background(), "game-1")
	if err != nil {
		t.Fatalf("finding bets: %v", err)
	}
	if len(bets) != 1 || bets[0].Status != bettracking.BetStatusWon {
		t.Errorf("expected settled bet to remain settled; got %+v", bets)
	}
}
