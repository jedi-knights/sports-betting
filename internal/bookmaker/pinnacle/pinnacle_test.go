package pinnacle_test

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/jedi-knights/sports-betting/internal/bookmaker"
	"github.com/jedi-knights/sports-betting/internal/bookmaker/pinnacle"
)

// newTestServer returns an httptest.Server that handles Pinnacle-shaped endpoints.
func newTestServer(t *testing.T, mux *http.ServeMux) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(mux)
	t.Cleanup(srv.Close)
	return srv
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(v)
}

// --- AccountManager ---

func TestPinnacleAccountManager_Balance(t *testing.T) {
	// Arrange
	mux := http.NewServeMux()
	mux.HandleFunc("GET /v1/client/balance", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, map[string]any{"availableBalance": 1234.56, "currency": "USD"})
	})
	srv := newTestServer(t, mux)

	am := pinnacle.NewAccountManager(pinnacle.Config{
		BaseURL:  srv.URL,
		Username: "user",
		Password: "pass",
	})

	// Act
	bal, err := am.Balance(context.Background())

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if bal != 1234.56 {
		t.Errorf("balance: want 1234.56, got %v", bal)
	}
}

func TestPinnacleAccountManager_MaxStake(t *testing.T) {
	// Arrange
	mux := http.NewServeMux()
	mux.HandleFunc("GET /v1/bets/straight/bet", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, map[string]any{"maxRiskStake": 500.0, "maxWinStake": 1000.0})
	})
	srv := newTestServer(t, mux)

	am := pinnacle.NewAccountManager(pinnacle.Config{
		BaseURL:  srv.URL,
		Username: "user",
		Password: "pass",
	})

	// Act
	max, err := am.MaxStake(context.Background(), "m1", "home")

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if max != 500.0 {
		t.Errorf("max stake: want 500.0, got %v", max)
	}
}

// --- BookmakerClient ---

func TestPinnacleClient_PlaceBet_Accepted(t *testing.T) {
	// Arrange
	mux := http.NewServeMux()
	mux.HandleFunc("POST /v2/bets/straight", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, map[string]any{
			"status": "ACCEPTED",
			"betId":  float64(9876543),
		})
	})
	srv := newTestServer(t, mux)

	client := pinnacle.NewClient(pinnacle.Config{
		BaseURL:  srv.URL,
		Username: "user",
		Password: "pass",
	})

	// Act
	resp, err := client.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID:        "event:889:1234:moneyline:home",
		MarketID:       "market-nfl-1",
		Side:           "home",
		RequestedStake: 25.0,
		DecimalOdds:    1.91,
	})

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.Rejected {
		t.Errorf("expected accepted, got rejected: %s", resp.RejectionReason)
	}
	if resp.BetID == "" {
		t.Errorf("expected non-empty BetID")
	}
	if resp.AcceptedStake != 25.0 {
		t.Errorf("stake: want 25.0, got %v", resp.AcceptedStake)
	}
}

func TestPinnacleClient_PlaceBet_PendingAcceptance(t *testing.T) {
	// Arrange — bookmaker returns PENDING_ACCEPTANCE; treated as accepted
	mux := http.NewServeMux()
	mux.HandleFunc("POST /v2/bets/straight", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, map[string]any{
			"status": "PENDING_ACCEPTANCE",
			"betId":  float64(111),
		})
	})
	srv := newTestServer(t, mux)

	client := pinnacle.NewClient(pinnacle.Config{BaseURL: srv.URL})

	// Act
	resp, _ := client.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID: "offer-1", MarketID: "m1", Side: "home", RequestedStake: 10, DecimalOdds: 2.0,
	})

	// Assert
	if resp.Rejected {
		t.Errorf("PENDING_ACCEPTANCE should not be rejected")
	}
}

func TestPinnacleClient_PlaceBet_Rejected(t *testing.T) {
	// Arrange — bookmaker returns a non-ACCEPTED status
	mux := http.NewServeMux()
	mux.HandleFunc("POST /v2/bets/straight", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, map[string]any{
			"status":       "NOT_ACCEPTED",
			"betId":        float64(0),
			"errorCode":    "LINE_CHANGED",
		})
	})
	srv := newTestServer(t, mux)

	client := pinnacle.NewClient(pinnacle.Config{BaseURL: srv.URL})

	// Act
	resp, _ := client.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID: "offer-1", MarketID: "m1", Side: "home", RequestedStake: 10, DecimalOdds: 2.0,
	})

	// Assert
	if !resp.Rejected {
		t.Errorf("expected rejection for NOT_ACCEPTED status")
	}
}

func TestPinnacleClient_GetOffers_ReturnsLinesAsOffers(t *testing.T) {
	// Arrange
	mux := http.NewServeMux()
	mux.HandleFunc("GET /v1/fixtures/special/markets", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, map[string]any{
			"leagues": []map[string]any{
				{
					"id": 889,
					"events": []map[string]any{
						{
							"id":       12345,
							"home":     "Patriots",
							"away":     "Chiefs",
							"lines": []map[string]any{
								{"side": "home", "price": 2.10, "maxBet": 300.0},
								{"side": "away", "price": 1.80, "maxBet": 300.0},
							},
						},
					},
				},
			},
		})
	})
	srv := newTestServer(t, mux)

	client := pinnacle.NewClient(pinnacle.Config{BaseURL: srv.URL})

	// Act
	offers, err := client.GetOffers(context.Background(), "12345")

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(offers) == 0 {
		t.Errorf("expected at least one offer for market 12345")
	}
}

// compile-time interface checks
var _ bookmaker.BookmakerClient = (*pinnacle.Client)(nil)
var _ bookmaker.AccountManager = (*pinnacle.AccountManager)(nil)
