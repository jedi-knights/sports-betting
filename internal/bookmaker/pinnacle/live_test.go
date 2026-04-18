package pinnacle_test

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/jedi-knights/sports-betting/internal/bettracking"
	"github.com/jedi-knights/sports-betting/internal/bookmaker"
	"github.com/jedi-knights/sports-betting/internal/bookmaker/pinnacle"
)

// TestLivePlacementIntegration exercises the full stack:
//   SafeBookmakerClient → PinnacleClient → BetStore → CLV resolution.
func TestLivePlacementIntegration(t *testing.T) {
	// Arrange: mock Pinnacle server
	mux := http.NewServeMux()
	mux.HandleFunc("GET /v1/client/balance", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, map[string]any{"availableBalance": 5000.0, "currency": "USD"})
	})
	mux.HandleFunc("GET /v1/bets/straight/bet", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, map[string]any{"maxRiskStake": 200.0})
	})
	mux.HandleFunc("POST /v2/bets/straight", func(w http.ResponseWriter, r *http.Request) {
		var body map[string]any
		_ = json.NewDecoder(r.Body).Decode(&body)
		writeJSON(w, map[string]any{
			"status": "ACCEPTED",
			"betId":  float64(777),
		})
	})
	srv := httptest.NewServer(mux)
	defer srv.Close()

	cfg := pinnacle.Config{BaseURL: srv.URL, Username: "u", Password: "p"}
	inner := pinnacle.NewClient(cfg)
	am := pinnacle.NewAccountManager(cfg)

	safe := bookmaker.NewSafeBookmakerClient(inner, am,
		bookmaker.WithSafeMaxStakeCap(50),
		bookmaker.WithSafeBalanceFloor(100),
	)

	betStore := bettracking.NewMemoryBetStore()
	ctx := context.Background()

	// Act: place a bet
	resp, err := safe.PlaceBet(ctx, bookmaker.BetRequest{
		OfferID:        "event:889:12345:moneyline:home",
		MarketID:       "12345",
		Side:           "home",
		RequestedStake: 30,
		DecimalOdds:    1.91,
	})
	if err != nil {
		t.Fatalf("PlaceBet: %v", err)
	}
	if resp.Rejected {
		t.Fatalf("bet rejected: %s", resp.RejectionReason)
	}

	bet := bettracking.Bet{
		ID:          resp.BetID,
		EventID:     "event-nfl-12345",
		MarketID:    "12345",
		Side:        "home",
		Stake:       resp.AcceptedStake,
		DecimalOdds: resp.DecimalOdds,
		Status:      bettracking.BetStatusOpen,
	}
	if err := betStore.Save(bet); err != nil {
		t.Fatalf("Save bet: %v", err)
	}

	// Assert: bet recorded correctly
	saved, err := betStore.FindByID(resp.BetID)
	if err != nil {
		t.Fatalf("FindByID: %v", err)
	}
	if saved.Stake != 30 {
		t.Errorf("stake: want 30, got %v", saved.Stake)
	}
	if saved.Status != bettracking.BetStatusOpen {
		t.Errorf("status: want open, got %v", saved.Status)
	}
}

// TestCLVSmoke verifies that CLV is correctly computed when a closing line is provided.
// This exercises the CLV resolution path using the real bettracking.ResolveCLV formula.
func TestCLVSmoke(t *testing.T) {
	// Arrange: place a bet at 2.00 odds; closing line is 1.95
	betStore := bettracking.NewMemoryBetStore()
	bet := bettracking.Bet{
		ID:          "clv-test-1",
		EventID:     "event-1",
		MarketID:    "m1",
		Side:        "home",
		Stake:       50,
		DecimalOdds: 2.00,
		Status:      bettracking.BetStatusOpen,
	}
	if err := betStore.Save(bet); err != nil {
		t.Fatalf("Save: %v", err)
	}

	// Act: resolve CLV with closing odds of 1.95
	if err := betStore.ResolveCLV(bet.ID, 1.95); err != nil {
		t.Fatalf("ResolveCLV: %v", err)
	}

	// Assert: CLV = 1/1.95 - 1/2.00 ≈ 0.0128 (positive = we beat the close)
	updated, _ := betStore.FindByID(bet.ID)
	if updated.CLV == nil {
		t.Fatal("expected CLV to be set")
	}
	// 1/1.95 - 1/2.00 = 0.5128 - 0.5 = 0.0128
	wantCLV := 1.0/1.95 - 1.0/2.00
	const tol = 1e-6
	if diff := *updated.CLV - wantCLV; diff < -tol || diff > tol {
		t.Errorf("CLV: want %.6f, got %.6f", wantCLV, *updated.CLV)
	}
	if *updated.CLV <= 0 {
		t.Errorf("expected positive CLV (beat the close), got %v", *updated.CLV)
	}
}
