// Package bookmaker defines the port interface for bookmaker interactions and provides
// a SimulatedBookmakerClient for paper trading.
package bookmaker

import (
	"context"
	"time"
)

// LineOffer is a bookmaker's current price offer for one side of a market.
// Offers are time-limited: PlaceBet will reject any offer past its ExpiresAt.
type LineOffer struct {
	OfferID     string
	MarketID    string
	Side        string
	DecimalOdds float64
	MaxStake    float64
	ExpiresAt   time.Time
}

// BetRequest is a request to place a bet against a specific offer.
// DecimalOdds carries the odds the client observed when fetching the offer; the
// bookmaker compares this to the current price to detect stale quotes.
type BetRequest struct {
	OfferID        string
	MarketID       string
	Side           string
	RequestedStake float64
	DecimalOdds    float64
}

// BetResponse is the bookmaker's response to a PlaceBet call.
type BetResponse struct {
	BetID           string
	AcceptedStake   float64
	DecimalOdds     float64
	// Filled is true when AcceptedStake == RequestedStake.
	Filled          bool
	Rejected        bool
	RejectionReason string
}

// BookmakerClient is the port for interacting with a bookmaker.
// Implementations include SimulatedBookmakerClient (paper trading) and
// live adapter implementations per bookmaker (live execution).
type BookmakerClient interface {
	// GetOffers returns current line offers for all configured sides of a market.
	GetOffers(ctx context.Context, marketID string) ([]LineOffer, error)
	// PlaceBet attempts to place a bet against a specific offer.
	// Bets may be partially filled or rejected; the caller must inspect Rejected.
	PlaceBet(ctx context.Context, req BetRequest) (BetResponse, error)
}

// AccountManager is the port for bookmaker account state.
// Implementations query account balance and per-market stake limits.
type AccountManager interface {
	// Balance returns the current available balance in the account's native currency.
	Balance(ctx context.Context) (float64, error)
	// MaxStake returns the bookmaker's maximum accepted stake for a given market and side.
	// This reflects current account-level limits; it may shrink over time as the account is limited.
	MaxStake(ctx context.Context, marketID, side string) (float64, error)
}
