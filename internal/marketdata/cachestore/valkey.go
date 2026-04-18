package cachestore

import (
	"context"
	"fmt"
	"time"

	"github.com/valkey-io/valkey-go"
)

// ValkeyCache implements Cache using the official valkey-go client.
// It uses RESP3 client-side caching (CSC): after the first network fetch,
// values are held in process memory and Valkey sends invalidation messages
// when the underlying key changes, eliminating redundant round-trips.
type ValkeyCache struct {
	client valkey.Client
}

// NewValkeyCache connects to the Valkey server at addr and returns a ValkeyCache.
func NewValkeyCache(addr string) (*ValkeyCache, error) {
	client, err := valkey.NewClient(valkey.ClientOption{
		InitAddress: []string{addr},
	})
	if err != nil {
		return nil, fmt.Errorf("connecting to valkey: %w", err)
	}
	return &ValkeyCache{client: client}, nil
}

// Get retrieves a value by key using client-side caching.
// Returns ("", false, nil) when the key does not exist.
func (c *ValkeyCache) Get(ctx context.Context, key string) (string, bool, error) {
	result, err := c.client.DoCache(ctx,
		c.client.B().Get().Key(key).Cache(),
		time.Minute,
	).ToString()
	if valkey.IsValkeyNil(err) {
		return "", false, nil
	}
	if err != nil {
		return "", false, err
	}
	return result, true, nil
}

// Set stores a key-value pair with the given TTL.
func (c *ValkeyCache) Set(ctx context.Context, key, value string, ttl time.Duration) error {
	return c.client.Do(ctx,
		c.client.B().Set().Key(key).Value(value).Ex(ttl).Build(),
	).Error()
}

// Del removes one or more keys.
func (c *ValkeyCache) Del(ctx context.Context, keys ...string) error {
	if len(keys) == 0 {
		return nil
	}
	return c.client.Do(ctx,
		c.client.B().Del().Key(keys...).Build(),
	).Error()
}

// Close releases the Valkey connection.
func (c *ValkeyCache) Close() {
	c.client.Close()
}
