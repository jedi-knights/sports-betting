package bookmaker_test

import (
	"context"
	"math"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/bookmaker"
)

const (
	testMarket = "m1"
	testSide   = "home"
	trueProb   = 0.50
	margin     = 0.05
)

func newClient(opts ...bookmaker.Option) *bookmaker.SimulatedBookmakerClient {
	return bookmaker.NewSimulatedBookmakerClient(opts...)
}

var fixedNow = time.Date(2024, 1, 1, 12, 0, 0, 0, time.UTC)

func withFixedNow(t time.Time) bookmaker.Option {
	return bookmaker.WithNow(func() time.Time { return t })
}

// --- GetOffers ---

func TestGetOffers_ReturnsEmptyForUnknownMarket(t *testing.T) {
	c := newClient(withFixedNow(fixedNow))
	offers, err := c.GetOffers(context.Background(), "unknown")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(offers) != 0 {
		t.Errorf("expected 0 offers, got %d", len(offers))
	}
}

func TestGetOffers_AppliesMarginToOdds(t *testing.T) {
	c := newClient(bookmaker.WithMargin(margin), bookmaker.WithMaxStake(100), withFixedNow(fixedNow))
	c.SetMarket(testMarket, testSide, trueProb)

	offers, err := c.GetOffers(context.Background(), testMarket)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(offers) != 1 {
		t.Fatalf("expected 1 offer, got %d", len(offers))
	}
	// trueProb=0.50, margin=0.05 → offered implied = 0.525 → odds = 1/0.525 ≈ 1.905
	wantOdds := 1.0 / (trueProb * (1.0 + margin))
	if math.Abs(offers[0].DecimalOdds-wantOdds) > 0.001 {
		t.Errorf("odds: want %.4f, got %.4f", wantOdds, offers[0].DecimalOdds)
	}
}

func TestGetOffers_MaxStakeFromConfig(t *testing.T) {
	c := newClient(bookmaker.WithMaxStake(250), withFixedNow(fixedNow))
	c.SetMarket(testMarket, testSide, trueProb)

	offers, _ := c.GetOffers(context.Background(), testMarket)
	if offers[0].MaxStake != 250 {
		t.Errorf("maxStake: want 250, got %v", offers[0].MaxStake)
	}
}

func TestGetOffers_ExpirySetFromTTL(t *testing.T) {
	ttl := 30 * time.Second
	c := newClient(bookmaker.WithOfferTTL(ttl), withFixedNow(fixedNow))
	c.SetMarket(testMarket, testSide, trueProb)

	offers, _ := c.GetOffers(context.Background(), testMarket)
	want := fixedNow.Add(ttl)
	if !offers[0].ExpiresAt.Equal(want) {
		t.Errorf("expiry: want %v, got %v", want, offers[0].ExpiresAt)
	}
}

// --- PlaceBet: acceptance ---

func TestPlaceBet_AcceptsValidBet(t *testing.T) {
	c := newClient(bookmaker.WithMaxStake(100), withFixedNow(fixedNow))
	c.SetMarket(testMarket, testSide, trueProb)

	offers, _ := c.GetOffers(context.Background(), testMarket)
	offer := offers[0]

	resp, err := c.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID:        offer.OfferID,
		MarketID:       offer.MarketID,
		Side:           offer.Side,
		RequestedStake: 50,
		DecimalOdds:    offer.DecimalOdds,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.Rejected {
		t.Errorf("expected accepted, got rejected: %s", resp.RejectionReason)
	}
	if resp.AcceptedStake != 50 {
		t.Errorf("stake: want 50, got %v", resp.AcceptedStake)
	}
}

// --- PlaceBet: partial fill ---

func TestPlaceBet_PartialFillWhenStakeExceedsMax(t *testing.T) {
	c := newClient(bookmaker.WithMaxStake(40), withFixedNow(fixedNow))
	c.SetMarket(testMarket, testSide, trueProb)

	offers, _ := c.GetOffers(context.Background(), testMarket)
	offer := offers[0]

	resp, _ := c.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID:        offer.OfferID,
		MarketID:       offer.MarketID,
		Side:           offer.Side,
		RequestedStake: 100,
		DecimalOdds:    offer.DecimalOdds,
	})
	if resp.Rejected {
		t.Errorf("expected partial fill, not rejection")
	}
	if resp.AcceptedStake != 40 {
		t.Errorf("stake: want 40, got %v", resp.AcceptedStake)
	}
	if resp.Filled {
		t.Errorf("expected Filled=false for partial fill")
	}
}

// --- PlaceBet: rejection (expired) ---

func TestPlaceBet_RejectsExpiredOffer(t *testing.T) {
	ttl := 30 * time.Second
	c := newClient(bookmaker.WithOfferTTL(ttl), bookmaker.WithMaxStake(100), withFixedNow(fixedNow))
	c.SetMarket(testMarket, testSide, trueProb)

	offers, _ := c.GetOffers(context.Background(), testMarket)
	offer := offers[0]

	// advance time past TTL
	c.SetNow(func() time.Time { return fixedNow.Add(ttl + time.Second) })

	resp, _ := c.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID:        offer.OfferID,
		MarketID:       offer.MarketID,
		Side:           offer.Side,
		RequestedStake: 50,
		DecimalOdds:    offer.DecimalOdds,
	})
	if !resp.Rejected {
		t.Errorf("expected rejection for expired offer")
	}
}

// --- PlaceBet: rejection (odds moved) ---

func TestPlaceBet_RejectsWhenOddsHaveMoved(t *testing.T) {
	c := newClient(
		bookmaker.WithMaxStake(100),
		bookmaker.WithOddsMoveTolerance(0.01),
		withFixedNow(fixedNow),
	)
	c.SetMarket(testMarket, testSide, trueProb)

	offers, _ := c.GetOffers(context.Background(), testMarket)
	offer := offers[0]

	// submit bet with stale odds (much worse than current)
	resp, _ := c.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID:        offer.OfferID,
		MarketID:       offer.MarketID,
		Side:           offer.Side,
		RequestedStake: 50,
		DecimalOdds:    offer.DecimalOdds + 0.50, // much better than offered — reject
	})
	if !resp.Rejected {
		t.Errorf("expected rejection for odds mismatch")
	}
}

// --- PlaceBet: unknown offer ---

func TestPlaceBet_RejectsUnknownOfferID(t *testing.T) {
	c := newClient(bookmaker.WithMaxStake(100), withFixedNow(fixedNow))
	c.SetMarket(testMarket, testSide, trueProb)

	resp, _ := c.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID:        "nonexistent",
		MarketID:       testMarket,
		Side:           testSide,
		RequestedStake: 50,
		DecimalOdds:    1.90,
	})
	if !resp.Rejected {
		t.Errorf("expected rejection for unknown offer")
	}
}

// --- Line movement ---

func TestPlaceBet_MovesLineAfterAcceptedBet(t *testing.T) {
	c := newClient(
		bookmaker.WithMaxStake(1000),
		bookmaker.WithLiquidity(100),
		withFixedNow(fixedNow),
	)
	c.SetMarket(testMarket, testSide, trueProb)

	offers1, _ := c.GetOffers(context.Background(), testMarket)
	oddsBefore := offers1[0].DecimalOdds

	c.PlaceBet(context.Background(), bookmaker.BetRequest{ //nolint:errcheck
		OfferID:        offers1[0].OfferID,
		MarketID:       offers1[0].MarketID,
		Side:           offers1[0].Side,
		RequestedStake: 50,
		DecimalOdds:    offers1[0].DecimalOdds,
	})

	offers2, _ := c.GetOffers(context.Background(), testMarket)
	oddsAfter := offers2[0].DecimalOdds

	// Betting on home should shorten home odds (lower decimal = shorter)
	if oddsAfter >= oddsBefore {
		t.Errorf("expected line movement: odds should shorten after bet; before=%.4f after=%.4f",
			oddsBefore, oddsAfter)
	}
}

// --- Account limiting ---

func TestPlaceBet_ReducesMaxStakeAfterNWins(t *testing.T) {
	winLimit := 3
	floor := 10.0
	c := newClient(
		bookmaker.WithMaxStake(100),
		bookmaker.WithMaxStakeFloor(floor),
		bookmaker.WithWinLimit(winLimit),
		withFixedNow(fixedNow),
	)
	c.SetMarket(testMarket, testSide, trueProb)

	for range winLimit {
		c.RecordWin()
	}

	offers, _ := c.GetOffers(context.Background(), testMarket)
	if offers[0].MaxStake != floor {
		t.Errorf("maxStake: want %v after %d wins, got %v", floor, winLimit, offers[0].MaxStake)
	}
}

func TestPlaceBet_MaxStakeUnchangedBeforeWinLimit(t *testing.T) {
	c := newClient(
		bookmaker.WithMaxStake(100),
		bookmaker.WithMaxStakeFloor(10),
		bookmaker.WithWinLimit(3),
		withFixedNow(fixedNow),
	)
	c.SetMarket(testMarket, testSide, trueProb)

	c.RecordWin() // only 1 win, limit is 3

	offers, _ := c.GetOffers(context.Background(), testMarket)
	if offers[0].MaxStake != 100 {
		t.Errorf("maxStake should remain 100 before win limit, got %v", offers[0].MaxStake)
	}
}

// compile-time check that SimulatedBookmakerClient satisfies the interface
var _ bookmaker.BookmakerClient = (*bookmaker.SimulatedBookmakerClient)(nil)
