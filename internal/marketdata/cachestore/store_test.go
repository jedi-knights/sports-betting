package cachestore_test

import (
	"context"
	"sync"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/cachestore"
)

// mapCache is a test double for cachestore.Cache.
type mapCache struct {
	mu   sync.RWMutex
	data map[string]string
	hits int
}

func newMapCache() *mapCache { return &mapCache{data: make(map[string]string)} }

func (c *mapCache) Get(_ context.Context, key string) (string, bool, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	v, ok := c.data[key]
	if ok {
		c.hits++
	}
	return v, ok, nil
}

func (c *mapCache) Set(_ context.Context, key, value string, _ time.Duration) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data[key] = value
	return nil
}

func (c *mapCache) Del(_ context.Context, keys ...string) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	for _, k := range keys {
		delete(c.data, k)
	}
	return nil
}

func TestCachingLineStore_LinesServedFromCache(t *testing.T) {
	backing := marketdata.NewMemoryLineStore()
	cache := newMapCache()
	store := cachestore.New(backing, cache, time.Minute)

	ctx := context.Background()
	ts := time.Now()
	lines := []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts},
	}
	if err := store.SaveLines(ctx, lines); err != nil {
		t.Fatalf("SaveLines: %v", err)
	}

	// First call populates the cache.
	got, err := store.Lines(ctx, "m1")
	if err != nil {
		t.Fatalf("Lines (miss): %v", err)
	}
	if len(got) != 1 {
		t.Fatalf("got %d lines, want 1", len(got))
	}

	// Second call should hit the cache without touching backing store.
	hitsBefore := cache.hits
	got2, err := store.Lines(ctx, "m1")
	if err != nil {
		t.Fatalf("Lines (hit): %v", err)
	}
	if len(got2) != 1 {
		t.Fatalf("got %d lines on cache hit, want 1", len(got2))
	}
	if cache.hits == hitsBefore {
		t.Fatal("expected cache hit on second Lines call, but cache was not consulted")
	}
}

func TestCachingLineStore_SaveLinesInvalidatesCache(t *testing.T) {
	backing := marketdata.NewMemoryLineStore()
	cache := newMapCache()
	store := cachestore.New(backing, cache, time.Minute)

	ctx := context.Background()
	ts := time.Now()

	if err := store.SaveLines(ctx, []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts},
	}); err != nil {
		t.Fatalf("first SaveLines: %v", err)
	}
	// Populate cache.
	if _, err := store.Lines(ctx, "m1"); err != nil {
		t.Fatalf("Lines: %v", err)
	}

	// Update the backing store via SaveLines — must invalidate cache.
	if err := store.SaveLines(ctx, []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts},
		{ID: "l2", MarketID: "m1", BookID: "b2", Side: marketdata.SideAway, RecordedAt: ts},
	}); err != nil {
		t.Fatalf("second SaveLines: %v", err)
	}

	got, err := store.Lines(ctx, "m1")
	if err != nil {
		t.Fatalf("Lines after invalidation: %v", err)
	}
	if len(got) != 2 {
		t.Fatalf("got %d lines after update, want 2 (cache not invalidated)", len(got))
	}
}

func TestCachingLineStore_Markets(t *testing.T) {
	backing := marketdata.NewMemoryLineStore()
	cache := newMapCache()
	store := cachestore.New(backing, cache, time.Minute)

	ctx := context.Background()
	ts := time.Now()
	if err := store.SaveLines(ctx, []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts},
		{ID: "l2", MarketID: "m2", BookID: "b1", Side: marketdata.SideAway, RecordedAt: ts},
	}); err != nil {
		t.Fatalf("SaveLines: %v", err)
	}

	ids, err := store.Markets(ctx)
	if err != nil {
		t.Fatalf("Markets: %v", err)
	}
	if len(ids) != 2 {
		t.Fatalf("got %d market IDs, want 2", len(ids))
	}

	// Second call should be a cache hit.
	hitsBefore := cache.hits
	if _, err := store.Markets(ctx); err != nil {
		t.Fatalf("Markets (hit): %v", err)
	}
	if cache.hits == hitsBefore {
		t.Fatal("expected cache hit on second Markets call")
	}
}

func TestCachingLineStore_ClosingLine(t *testing.T) {
	backing := marketdata.NewMemoryLineStore()
	cache := newMapCache()
	store := cachestore.New(backing, cache, time.Minute)

	ctx := context.Background()
	ts := time.Now()
	if err := store.SaveLines(ctx, []marketdata.Line{
		{ID: "cl1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome,
			RecordedAt: ts, IsClosing: true},
	}); err != nil {
		t.Fatalf("SaveLines: %v", err)
	}

	line, err := store.ClosingLine(ctx, "m1", marketdata.SideHome)
	if err != nil || line == nil {
		t.Fatalf("ClosingLine: err=%v line=%v", err, line)
	}

	hitsBefore := cache.hits
	line2, err := store.ClosingLine(ctx, "m1", marketdata.SideHome)
	if err != nil || line2 == nil {
		t.Fatalf("ClosingLine (hit): err=%v line=%v", err, line2)
	}
	if cache.hits == hitsBefore {
		t.Fatal("expected cache hit on second ClosingLine call")
	}
}
