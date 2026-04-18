package bettracking

import (
	"context"
	"fmt"
	"sync"
)

// MemoryBetStore is a thread-safe in-memory BetStore for backtesting and tests.
type MemoryBetStore struct {
	mu    sync.RWMutex
	bets  map[string]Bet
	order []string
}

// NewMemoryBetStore returns an empty MemoryBetStore.
func NewMemoryBetStore() *MemoryBetStore {
	return &MemoryBetStore{bets: make(map[string]Bet)}
}

// Save stores a new bet. Returns ErrDuplicateID if the ID already exists.
func (s *MemoryBetStore) Save(_ context.Context, bet Bet) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, exists := s.bets[bet.ID]; exists {
		return fmt.Errorf("%w: %s", ErrDuplicateID, bet.ID)
	}
	s.bets[bet.ID] = bet
	s.order = append(s.order, bet.ID)
	return nil
}

// FindByID returns the bet with the given ID. Returns ErrNotFound if absent.
func (s *MemoryBetStore) FindByID(_ context.Context, id string) (Bet, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	bet, ok := s.bets[id]
	if !ok {
		return Bet{}, fmt.Errorf("%w: %s", ErrNotFound, id)
	}
	return bet, nil
}

// FindAll returns all bets in insertion order.
func (s *MemoryBetStore) FindAll(_ context.Context) ([]Bet, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := make([]Bet, 0, len(s.order))
	for _, id := range s.order {
		out = append(out, s.bets[id])
	}
	return out, nil
}

// FindByStatus returns all bets matching the given status.
func (s *MemoryBetStore) FindByStatus(_ context.Context, status BetStatus) ([]Bet, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	var out []Bet
	for _, id := range s.order {
		if b := s.bets[id]; b.Status == status {
			out = append(out, b)
		}
	}
	return out, nil
}

// Update replaces an existing bet. Returns ErrNotFound if the ID is absent.
func (s *MemoryBetStore) Update(_ context.Context, bet Bet) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.bets[bet.ID]; !ok {
		return fmt.Errorf("%w: %s", ErrNotFound, bet.ID)
	}
	s.bets[bet.ID] = bet
	return nil
}

// FindByEventID returns all bets associated with the given event ID.
func (s *MemoryBetStore) FindByEventID(_ context.Context, eventID string) ([]Bet, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	var out []Bet
	for _, id := range s.order {
		if b := s.bets[id]; b.EventID == eventID {
			out = append(out, b)
		}
	}
	return out, nil
}

// Resolve marks a bet won or lost based on the game outcome.
func (s *MemoryBetStore) Resolve(_ context.Context, betID string, won bool) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	bet, ok := s.bets[betID]
	if !ok {
		return fmt.Errorf("%w: %s", ErrNotFound, betID)
	}
	if won {
		bet.Status = BetStatusWon
	} else {
		bet.Status = BetStatusLost
	}
	s.bets[betID] = bet
	return nil
}

// ResolveCLV computes and stores the closing line value.
// CLV = (1/closingOdds) − (1/betOdds). Positive means the bet beat the close.
// Returns an error if closingDecimalOdds or the bet's DecimalOdds are not positive.
func (s *MemoryBetStore) ResolveCLV(_ context.Context, betID string, closingDecimalOdds float64) error {
	if closingDecimalOdds <= 0 {
		return fmt.Errorf("ResolveCLV: closingDecimalOdds must be positive, got %v", closingDecimalOdds)
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	bet, ok := s.bets[betID]
	if !ok {
		return fmt.Errorf("%w: %s", ErrNotFound, betID)
	}
	if bet.DecimalOdds <= 0 {
		return fmt.Errorf("ResolveCLV: bet %s has invalid DecimalOdds %v", betID, bet.DecimalOdds)
	}
	clv := 1.0/closingDecimalOdds - 1.0/bet.DecimalOdds
	bet.CLV = &clv
	s.bets[betID] = bet
	return nil
}
