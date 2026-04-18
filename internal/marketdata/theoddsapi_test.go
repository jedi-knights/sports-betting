package marketdata_test

import (
	"context"
	"encoding/json"
	"math"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

// scoresAPIFixture is a minimal The Odds API v4 scores response with one completed NFL game.
var scoresAPIFixture = []map[string]any{
	{
		"id":            "event1",
		"sport_key":     "americanfootball_nfl",
		"commence_time": "2024-09-05T23:20:00Z",
		"completed":     true,
		"home_team":     "Kansas City Chiefs",
		"away_team":     "Baltimore Ravens",
		"scores": []map[string]any{
			{"name": "Kansas City Chiefs", "score": "27"},
			{"name": "Baltimore Ravens", "score": "20"},
		},
		"last_update": "2024-09-06T02:00:00Z",
	},
	{
		"id":            "event2",
		"sport_key":     "americanfootball_nfl",
		"commence_time": "2024-09-06T20:00:00Z",
		"completed":     false,
		"home_team":     "Dallas Cowboys",
		"away_team":     "New York Giants",
		"scores":        nil,
		"last_update":   nil,
	},
}

func newScoresAPIServer(t *testing.T) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Validate the path contains the sport key.
		if r.URL.Path == "" {
			http.Error(w, "bad path", http.StatusBadRequest)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(scoresAPIFixture); err != nil {
			http.Error(w, "encode error", http.StatusInternalServerError)
		}
	}))
}

// oddsAPIFixture is a minimal The Odds API v4 odds response with one NFL event
// and one bookmaker offering h2h, spreads, and totals.
var oddsAPIFixture = []map[string]any{
	{
		"id":            "event1",
		"sport_key":     "americanfootball_nfl",
		"sport_title":   "NFL",
		"commence_time": "2024-09-05T23:20:00Z",
		"home_team":     "Kansas City Chiefs",
		"away_team":     "Baltimore Ravens",
		"bookmakers": []map[string]any{
			{
				"key":         "draftkings",
				"title":       "DraftKings",
				"last_update": "2024-09-05T20:00:00Z",
				"markets": []map[string]any{
					{
						"key":         "h2h",
						"last_update": "2024-09-05T20:00:00Z",
						"outcomes": []map[string]any{
							{"name": "Kansas City Chiefs", "price": -150},
							{"name": "Baltimore Ravens", "price": 130},
						},
					},
					{
						"key":         "spreads",
						"last_update": "2024-09-05T20:00:00Z",
						"outcomes": []map[string]any{
							{"name": "Kansas City Chiefs", "price": -110, "point": -3.5},
							{"name": "Baltimore Ravens", "price": -110, "point": 3.5},
						},
					},
					{
						"key":         "totals",
						"last_update": "2024-09-05T20:00:00Z",
						"outcomes": []map[string]any{
							{"name": "Over", "price": -110, "point": 47.5},
							{"name": "Under", "price": -110, "point": 47.5},
						},
					},
				},
			},
		},
	},
}

func newOddsAPIServer(t *testing.T) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(oddsAPIFixture); err != nil {
			http.Error(w, "encode error", http.StatusInternalServerError)
		}
	}))
}

func TestTheOddsAPIProvider(t *testing.T) {
	ctx := context.Background()

	// Arrange
	srv := newOddsAPIServer(t)
	t.Cleanup(srv.Close)
	p := marketdata.NewTheOddsAPIProvider("test-key", marketdata.WithBaseURL(srv.URL))

	t.Run("Events returns event matching sport and season", func(t *testing.T) {
		// Act
		events, err := p.Events(ctx, marketdata.SportNFL, "2024")

		// Assert
		if err != nil {
			t.Fatalf("Events: %v", err)
		}
		if len(events) != 1 {
			t.Fatalf("Events() count = %d, want 1", len(events))
		}
		e := events[0]
		if e.ID != "event1" {
			t.Errorf("Event.ID = %q, want %q", e.ID, "event1")
		}
		if e.HomeTeam != "Kansas City Chiefs" {
			t.Errorf("Event.HomeTeam = %q, want %q", e.HomeTeam, "Kansas City Chiefs")
		}
		if e.AwayTeam != "Baltimore Ravens" {
			t.Errorf("Event.AwayTeam = %q, want %q", e.AwayTeam, "Baltimore Ravens")
		}
		if e.Sport != marketdata.SportNFL {
			t.Errorf("Event.Sport = %q, want %q", e.Sport, marketdata.SportNFL)
		}
		if e.Season != "2024" {
			t.Errorf("Event.Season = %q, want %q", e.Season, "2024")
		}
	})

	t.Run("Events returns empty for wrong season", func(t *testing.T) {
		// Act
		events, err := p.Events(ctx, marketdata.SportNFL, "2023")

		// Assert
		if err != nil {
			t.Fatalf("Events: %v", err)
		}
		if len(events) != 0 {
			t.Errorf("Events() count = %d, want 0", len(events))
		}
	})

	t.Run("Markets returns all market types for event", func(t *testing.T) {
		// Arrange — seed the cache
		if _, err := p.Events(ctx, marketdata.SportNFL, "2024"); err != nil {
			t.Fatalf("Events (setup): %v", err)
		}

		// Act
		markets, err := p.Markets(ctx, "event1")

		// Assert
		if err != nil {
			t.Fatalf("Markets: %v", err)
		}
		if len(markets) != 3 {
			t.Fatalf("Markets() count = %d, want 3 (moneyline, spread, total)", len(markets))
		}
		seen := make(map[marketdata.MarketType]bool)
		for _, m := range markets {
			seen[m.Type] = true
		}
		for _, want := range []marketdata.MarketType{
			marketdata.MarketTypeMoneyline,
			marketdata.MarketTypeSpread,
			marketdata.MarketTypeTotal,
		} {
			if !seen[want] {
				t.Errorf("market type %q missing", want)
			}
		}
	})

	t.Run("Lines for moneyline market are devigged and sum to 1", func(t *testing.T) {
		// Arrange — seed the cache and find the moneyline market
		if _, err := p.Events(ctx, marketdata.SportNFL, "2024"); err != nil {
			t.Fatalf("Events (setup): %v", err)
		}
		markets, err := p.Markets(ctx, "event1")
		if err != nil {
			t.Fatalf("Markets (setup): %v", err)
		}
		var mlMarketID string
		for _, m := range markets {
			if m.Type == marketdata.MarketTypeMoneyline {
				mlMarketID = m.ID
			}
		}
		if mlMarketID == "" {
			t.Fatal("moneyline market not found in cache")
		}

		// Act
		lines, err := p.Lines(ctx, mlMarketID)

		// Assert
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		if len(lines) != 2 {
			t.Fatalf("Lines() count = %d, want 2", len(lines))
		}
		for _, l := range lines {
			if l.DecimalOdds == 0 {
				t.Errorf("line %q: DecimalOdds not set", l.ID)
			}
			if l.RawImpliedProb == 0 {
				t.Errorf("line %q: RawImpliedProb not set", l.ID)
			}
			if l.ImpliedProb == 0 {
				t.Errorf("line %q: ImpliedProb not devigged", l.ID)
			}
		}
		var sum float64
		for _, l := range lines {
			sum += l.ImpliedProb
		}
		if math.Abs(sum-1.0) > 1e-9 {
			t.Errorf("ImpliedProb sum = %v, want 1.0", sum)
		}
	})

	t.Run("Lines for spread market include point values", func(t *testing.T) {
		// Arrange
		if _, err := p.Events(ctx, marketdata.SportNFL, "2024"); err != nil {
			t.Fatalf("Events (setup): %v", err)
		}
		markets, err := p.Markets(ctx, "event1")
		if err != nil {
			t.Fatalf("Markets (setup): %v", err)
		}
		var spreadMarketID string
		for _, m := range markets {
			if m.Type == marketdata.MarketTypeSpread {
				spreadMarketID = m.ID
			}
		}
		if spreadMarketID == "" {
			t.Fatal("spread market not found in cache")
		}

		// Act
		lines, err := p.Lines(ctx, spreadMarketID)

		// Assert
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		if len(lines) == 0 {
			t.Fatal("Lines() returned empty for spread market")
		}
		for _, l := range lines {
			if l.Spread == nil {
				t.Errorf("line %q: Spread is nil", l.ID)
			}
		}
	})

	t.Run("Lines for totals market include over and under sides with total values", func(t *testing.T) {
		// Arrange
		if _, err := p.Events(ctx, marketdata.SportNFL, "2024"); err != nil {
			t.Fatalf("Events (setup): %v", err)
		}
		markets, err := p.Markets(ctx, "event1")
		if err != nil {
			t.Fatalf("Markets (setup): %v", err)
		}
		var totalsMarketID string
		for _, m := range markets {
			if m.Type == marketdata.MarketTypeTotal {
				totalsMarketID = m.ID
			}
		}
		if totalsMarketID == "" {
			t.Fatal("totals market not found in cache")
		}

		// Act
		lines, err := p.Lines(ctx, totalsMarketID)

		// Assert
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		sides := make(map[marketdata.Side]bool)
		for _, l := range lines {
			sides[l.Side] = true
			if l.Total == nil {
				t.Errorf("line %q: Total is nil", l.ID)
			}
		}
		if !sides[marketdata.SideOver] {
			t.Error("SideOver missing from totals market")
		}
		if !sides[marketdata.SideUnder] {
			t.Error("SideUnder missing from totals market")
		}
	})

	t.Run("Events returns error for unsupported sport", func(t *testing.T) {
		// Act
		_, err := p.Events(ctx, marketdata.Sport("cricket"), "2024")

		// Assert
		if err == nil {
			t.Error("expected error for unsupported sport, got nil")
		}
	})

	t.Run("Books returns classified books seen in last refresh", func(t *testing.T) {
		// Arrange — seed the cache
		if _, err := p.Events(ctx, marketdata.SportNFL, "2024"); err != nil {
			t.Fatalf("Events (setup): %v", err)
		}

		// Act
		books, err := p.Books(ctx)

		// Assert
		if err != nil {
			t.Fatalf("Books: %v", err)
		}
		if len(books) != 1 {
			t.Fatalf("Books() count = %d, want 1", len(books))
		}
		b := books[0]
		if b.ID != "draftkings" {
			t.Errorf("Book.ID = %q, want %q", b.ID, "draftkings")
		}
		if b.Type != marketdata.BookTypeSoft {
			t.Errorf("Book.Type = %q, want %q", b.Type, marketdata.BookTypeSoft)
		}
	})
}

func TestTheOddsAPIProvider_Scores(t *testing.T) {
	ctx := context.Background()

	// Arrange
	srv := newScoresAPIServer(t)
	t.Cleanup(srv.Close)
	p := marketdata.NewTheOddsAPIProvider("test-key", marketdata.WithBaseURL(srv.URL))

	// Act
	results, err := p.Scores(ctx, marketdata.SportNFL, 1)

	// Assert
	if err != nil {
		t.Fatalf("Scores: %v", err)
	}
	// Only completed events should be returned.
	if len(results) != 1 {
		t.Fatalf("Scores() count = %d, want 1 (only completed games)", len(results))
	}
	r := results[0]
	if r.EventID != "event1" {
		t.Errorf("GameResult.EventID = %q, want %q", r.EventID, "event1")
	}
	if r.HomeTeam != "Kansas City Chiefs" {
		t.Errorf("GameResult.HomeTeam = %q, want %q", r.HomeTeam, "Kansas City Chiefs")
	}
	if r.AwayTeam != "Baltimore Ravens" {
		t.Errorf("GameResult.AwayTeam = %q, want %q", r.AwayTeam, "Baltimore Ravens")
	}
	if r.HomeScore != 27 {
		t.Errorf("GameResult.HomeScore = %d, want 27", r.HomeScore)
	}
	if r.AwayScore != 20 {
		t.Errorf("GameResult.AwayScore = %d, want 20", r.AwayScore)
	}
	if r.WinningSide() != marketdata.SideHome {
		t.Errorf("WinningSide() = %q, want home", r.WinningSide())
	}
}
