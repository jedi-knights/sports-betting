package bookmaker_test

import (
	"context"
	"testing"

	"github.com/jedi-knights/sports-betting/internal/bettracking"
	"github.com/jedi-knights/sports-betting/internal/bookmaker"
)

// TestPaperTradingLoop verifies the end-to-end paper trading flow:
// SetMarket → GetOffers → PlaceBet → record bet → performance report.
func TestPaperTradingLoop(t *testing.T) {
	// Arrange
	book := bookmaker.NewSimulatedBookmakerClient(
		bookmaker.WithMargin(0.05),
		bookmaker.WithMaxStake(50),
		bookmaker.WithLiquidity(200),
		withFixedNow(fixedNow),
	)
	book.SetMarket("mkt-nfl-1", "home", 0.55)
	book.SetMarket("mkt-nfl-1", "away", 0.45)

	betStore := bettracking.NewMemoryBetStore()
	ctx := context.Background()

	// Act: get offers and place a bet on the home side
	offers, err := book.GetOffers(ctx, "mkt-nfl-1")
	if err != nil {
		t.Fatalf("GetOffers: %v", err)
	}
	var homeOffer bookmaker.LineOffer
	for _, o := range offers {
		if o.Side == "home" {
			homeOffer = o
		}
	}
	if homeOffer.OfferID == "" {
		t.Fatal("no home offer found")
	}

	resp, err := book.PlaceBet(ctx, bookmaker.BetRequest{
		OfferID:        homeOffer.OfferID,
		MarketID:       homeOffer.MarketID,
		Side:           homeOffer.Side,
		RequestedStake: 30,
		DecimalOdds:    homeOffer.DecimalOdds,
	})
	if err != nil {
		t.Fatalf("PlaceBet: %v", err)
	}
	if resp.Rejected {
		t.Fatalf("bet rejected: %s", resp.RejectionReason)
	}

	bet := bettracking.Bet{
		ID:          resp.BetID,
		EventID:     "event-nfl-1",
		MarketID:    homeOffer.MarketID,
		Side:        homeOffer.Side,
		Stake:       resp.AcceptedStake,
		DecimalOdds: resp.DecimalOdds,
		Status:      bettracking.BetStatusOpen,
	}
	if err := betStore.Save(ctx, bet); err != nil {
		t.Fatalf("Save bet: %v", err)
	}

	// Simulate a win: resolve the bet.
	if err := betStore.Resolve(ctx, bet.ID, true); err != nil {
		t.Fatalf("Resolve bet: %v", err)
	}
	book.RecordWin()

	// Assert: performance report shows 1 won bet with positive P&L.
	bets, _ := betStore.FindAll(ctx)
	results := make([]bettracking.BetResult, 0, len(bets))
	for _, b := range bets {
		results = append(results, bettracking.NewBetResult(b))
	}
	report := bettracking.ComputePerformanceReport(results)

	if report.TotalBets != 1 {
		t.Errorf("total_bets: want 1, got %d", report.TotalBets)
	}
	if report.WonBets != 1 {
		t.Errorf("won_bets: want 1, got %d", report.WonBets)
	}
	if report.TotalProfit <= 0 {
		t.Errorf("expected positive profit, got %v", report.TotalProfit)
	}
	if report.ROI <= 0 {
		t.Errorf("expected positive ROI, got %v", report.ROI)
	}
}
