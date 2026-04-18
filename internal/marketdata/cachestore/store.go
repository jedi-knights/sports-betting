// Package cachestore provides a caching LineStore that sits in front of a
// backing store using the Proxy pattern.  Reads are served from the cache where
// available; SaveLines writes through to the backing store and then invalidates
// the affected cache keys so subsequent reads reflect the latest data.
//
// The Cache interface is intentionally small so the production Valkey
// implementation and the in-memory test double are both trivial to write.
package cachestore

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

// Cache is the minimal set of operations required by CachingLineStore.
// The production implementation wraps valkey-go; the test double uses a map.
type Cache interface {
	Get(ctx context.Context, key string) (value string, found bool, err error)
	Set(ctx context.Context, key, value string, ttl time.Duration) error
	Del(ctx context.Context, keys ...string) error
}

var _ marketdata.LineStore = (*CachingLineStore)(nil)

// CachingLineStore wraps a LineStore with a Cache to reduce repeated reads
// against the backing store (typically Postgres).
type CachingLineStore struct {
	backing marketdata.LineStore
	cache   Cache
	ttl     time.Duration
}

// New returns a CachingLineStore backed by the given store and cache.
// ttl controls how long cached values are retained before expiry.
func New(backing marketdata.LineStore, cache Cache, ttl time.Duration) *CachingLineStore {
	return &CachingLineStore{backing: backing, cache: cache, ttl: ttl}
}

// SaveLines writes through to the backing store, then invalidates the cache
// entries for each affected market so subsequent reads return fresh data.
func (s *CachingLineStore) SaveLines(ctx context.Context, lines []marketdata.Line) error {
	if err := s.backing.SaveLines(ctx, lines); err != nil {
		return err
	}
	keys := make([]string, 0, len(lines)+1)
	seen := make(map[string]struct{}, len(lines))
	for _, l := range lines {
		if _, ok := seen[l.MarketID]; ok {
			continue
		}
		seen[l.MarketID] = struct{}{}
		keys = append(keys, linesKey(l.MarketID), closingKey(l.MarketID, string(l.Side)))
	}
	keys = append(keys, marketsKey)
	return s.cache.Del(ctx, keys...)
}

// Lines returns all stored lines for the market, serving from cache where available.
func (s *CachingLineStore) Lines(ctx context.Context, marketID string) ([]marketdata.Line, error) {
	key := linesKey(marketID)
	if raw, ok, err := s.cache.Get(ctx, key); err == nil && ok {
		var lines []marketdata.Line
		if err := json.Unmarshal([]byte(raw), &lines); err == nil {
			return lines, nil
		}
	}
	lines, err := s.backing.Lines(ctx, marketID)
	if err != nil {
		return nil, err
	}
	if raw, err := json.Marshal(lines); err == nil {
		_ = s.cache.Set(ctx, key, string(raw), s.ttl)
	}
	return lines, nil
}

// ClosingLine returns the most recent closing line, serving from cache where available.
func (s *CachingLineStore) ClosingLine(ctx context.Context, marketID string, side marketdata.Side) (*marketdata.Line, error) {
	key := closingKey(marketID, string(side))
	if raw, ok, err := s.cache.Get(ctx, key); err == nil && ok {
		var line marketdata.Line
		if err := json.Unmarshal([]byte(raw), &line); err == nil {
			return &line, nil
		}
	}
	line, err := s.backing.ClosingLine(ctx, marketID, side)
	if err != nil {
		return nil, err
	}
	if line != nil {
		if raw, err := json.Marshal(line); err == nil {
			_ = s.cache.Set(ctx, key, string(raw), s.ttl)
		}
	}
	return line, nil
}

// Markets returns the distinct market IDs, serving from cache where available.
func (s *CachingLineStore) Markets(ctx context.Context) ([]string, error) {
	if raw, ok, err := s.cache.Get(ctx, marketsKey); err == nil && ok {
		var ids []string
		if err := json.Unmarshal([]byte(raw), &ids); err == nil {
			return ids, nil
		}
	}
	ids, err := s.backing.Markets(ctx)
	if err != nil {
		return nil, err
	}
	if raw, err := json.Marshal(ids); err == nil {
		_ = s.cache.Set(ctx, marketsKey, string(raw), s.ttl)
	}
	return ids, nil
}

const marketsKey = "marketdata:markets"

func linesKey(marketID string) string   { return fmt.Sprintf("marketdata:lines:%s", marketID) }
func closingKey(mID, side string) string { return fmt.Sprintf("marketdata:closing:%s:%s", mID, side) }
