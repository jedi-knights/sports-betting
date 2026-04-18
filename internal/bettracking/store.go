package bettracking

import (
	"context"
	"errors"
)

// ErrNotFound is returned when a bet ID is not present in the store.
var ErrNotFound = errors.New("bet not found")

// ErrDuplicateID is returned when saving a bet whose ID already exists.
var ErrDuplicateID = errors.New("bet ID already exists")

// BetStore persists and retrieves bet signals.
// All methods accept a context so implementations can honour cancellation
// and deadline propagation — especially important for database-backed stores.
type BetStore interface {
	Save(ctx context.Context, bet Bet) error
	FindByID(ctx context.Context, id string) (Bet, error)
	FindAll(ctx context.Context) ([]Bet, error)
	FindByStatus(ctx context.Context, status BetStatus) ([]Bet, error)
	Update(ctx context.Context, bet Bet) error
	// FindByEventID returns all bets for the given event ID.
	FindByEventID(ctx context.Context, eventID string) ([]Bet, error)
	// Resolve marks a bet as won or lost based on the game outcome.
	Resolve(ctx context.Context, betID string, won bool) error
	// ResolveCLV computes and stores closing line value for a bet.
	// Returns an error if closingDecimalOdds is not positive.
	ResolveCLV(ctx context.Context, betID string, closingDecimalOdds float64) error
}
