package bettracking

import "errors"

// ErrNotFound is returned when a bet ID is not present in the store.
var ErrNotFound = errors.New("bet not found")

// ErrDuplicateID is returned when saving a bet whose ID already exists.
var ErrDuplicateID = errors.New("bet ID already exists")

// BetStore persists and retrieves bet signals.
type BetStore interface {
	Save(bet Bet) error
	FindByID(id string) (Bet, error)
	FindAll() ([]Bet, error)
	FindByStatus(status BetStatus) ([]Bet, error)
	Update(bet Bet) error
	// Resolve marks a bet as won or lost.
	Resolve(betID string, won bool) error
	// ResolveCLV computes and stores closing line value for a bet.
	ResolveCLV(betID string, closingDecimalOdds float64) error
}
