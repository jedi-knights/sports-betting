package bookmaker

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// SafeOption configures a SafeBookmakerClient.
type SafeOption func(*SafeBookmakerClient)

// WithSafeMaxStakeCap sets the hard cap on stake forwarded to the inner client.
// Any RequestedStake above this value is silently reduced before forwarding.
func WithSafeMaxStakeCap(cap float64) SafeOption {
	return func(c *SafeBookmakerClient) { c.maxStakeCap = cap }
}

// WithSafeBalanceFloor sets the minimum account balance required to place a bet.
// If the current balance is at or below this floor, the bet is rejected without
// contacting the inner client.
func WithSafeBalanceFloor(floor float64) SafeOption {
	return func(c *SafeBookmakerClient) { c.balanceFloor = floor }
}

// WithSafeDedupTTL sets how long a placed market+side combination is considered
// a duplicate. A second bet on the same market and side within this window is
// rejected to prevent double-betting on the same opportunity.
func WithSafeDedupTTL(d time.Duration) SafeOption {
	return func(c *SafeBookmakerClient) { c.dedupTTL = d }
}

// WithSafeNow injects a clock function for deterministic time-based tests.
func WithSafeNow(f func() time.Time) SafeOption {
	return func(c *SafeBookmakerClient) { c.now = f }
}

// SafeBookmakerClient is a Decorator around any BookmakerClient that enforces
// three bet-placement safety invariants before forwarding to the inner client:
//
//  1. Maximum stake cap — RequestedStake is clamped to maxStakeCap.
//  2. Account balance floor — the bet is rejected if Balance() ≤ balanceFloor.
//  3. Duplicate bet guard — a second bet on the same market+side within dedupTTL
//     is rejected to prevent re-betting the same opportunity.
//
// Safe for concurrent use.
type SafeBookmakerClient struct {
	inner   BookmakerClient
	manager AccountManager

	maxStakeCap  float64
	balanceFloor float64
	dedupTTL     time.Duration
	now          func() time.Time

	mu         sync.Mutex
	recentBets map[string]time.Time // "marketID:side" → placed-at
}

// NewSafeBookmakerClient wraps inner with safety checks driven by manager.
func NewSafeBookmakerClient(
	inner BookmakerClient,
	manager AccountManager,
	opts ...SafeOption,
) *SafeBookmakerClient {
	c := &SafeBookmakerClient{
		inner:        inner,
		manager:      manager,
		maxStakeCap:  1000,
		balanceFloor: 0,
		dedupTTL:     5 * time.Minute,
		now:          time.Now,
		recentBets:   make(map[string]time.Time),
	}
	for _, o := range opts {
		o(c)
	}
	return c
}

// GetOffers delegates directly to the inner client — no safety checks apply.
func (s *SafeBookmakerClient) GetOffers(ctx context.Context, marketID string) ([]LineOffer, error) {
	return s.inner.GetOffers(ctx, marketID)
}

// PlaceBet applies safety checks and, if all pass, forwards to the inner client.
func (s *SafeBookmakerClient) PlaceBet(ctx context.Context, req BetRequest) (BetResponse, error) {
	// --- 1. Balance floor check ---
	balance, err := s.manager.Balance(ctx)
	if err != nil {
		return BetResponse{Rejected: true, RejectionReason: fmt.Sprintf("balance check failed: %v", err)}, nil
	}
	if balance <= s.balanceFloor {
		return BetResponse{
			Rejected:        true,
			RejectionReason: fmt.Sprintf("balance %.2f is at or below floor %.2f", balance, s.balanceFloor),
		}, nil
	}

	// --- 2. Duplicate bet guard ---
	key := req.MarketID + ":" + req.Side
	s.mu.Lock()
	if placedAt, ok := s.recentBets[key]; ok {
		if s.now().Sub(placedAt) < s.dedupTTL {
			s.mu.Unlock()
			return BetResponse{
				Rejected:        true,
				RejectionReason: fmt.Sprintf("duplicate bet on %s within dedup TTL", key),
			}, nil
		}
	}
	s.mu.Unlock()

	// --- 3. Stake cap ---
	if req.RequestedStake > s.maxStakeCap {
		req.RequestedStake = s.maxStakeCap
	}

	resp, err := s.inner.PlaceBet(ctx, req)
	if err != nil || resp.Rejected {
		return resp, err
	}

	// Record this bet for dedup tracking only on successful placement.
	s.mu.Lock()
	s.recentBets[key] = s.now()
	s.mu.Unlock()

	return resp, nil
}
