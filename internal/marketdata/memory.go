package marketdata

import (
	"context"
	"sync"
)

var _ LineStore = (*memoryLineStore)(nil)

type memoryLineStore struct {
	mu      sync.RWMutex
	lines   map[string][]Line // key: marketID
	markets map[string]struct{}
}

// NewMemoryLineStore returns a LineStore that holds all lines in memory.
// It is used in tests and backtesting where persistence is not required.
func NewMemoryLineStore() LineStore {
	return &memoryLineStore{
		lines:   make(map[string][]Line),
		markets: make(map[string]struct{}),
	}
}

func (s *memoryLineStore) SaveLines(_ context.Context, lines []Line) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, l := range lines {
		s.lines[l.MarketID] = append(s.lines[l.MarketID], l)
		s.markets[l.MarketID] = struct{}{}
	}
	return nil
}

func (s *memoryLineStore) Markets(_ context.Context) ([]string, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := make([]string, 0, len(s.markets))
	for id := range s.markets {
		result = append(result, id)
	}
	return result, nil
}

func (s *memoryLineStore) Lines(_ context.Context, marketID string) ([]Line, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	src := s.lines[marketID]
	result := make([]Line, len(src))
	copy(result, src)
	return result, nil
}

func (s *memoryLineStore) ClosingLine(_ context.Context, marketID string, side Side) (*Line, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	for _, l := range s.lines[marketID] {
		if l.IsClosing && l.Side == side {
			lCopy := l
			return &lCopy, nil
		}
	}
	return nil, nil
}
