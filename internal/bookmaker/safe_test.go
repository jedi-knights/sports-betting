package bookmaker_test

import (
	"context"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/bookmaker"
)

// --- fakes ---

type fakeBetClient struct {
	resp bookmaker.BetResponse
	err  error
	reqs []bookmaker.BetRequest
}

func (f *fakeBetClient) GetOffers(_ context.Context, _ string) ([]bookmaker.LineOffer, error) {
	return nil, nil
}
func (f *fakeBetClient) PlaceBet(_ context.Context, req bookmaker.BetRequest) (bookmaker.BetResponse, error) {
	f.reqs = append(f.reqs, req)
	return f.resp, f.err
}

// concurrentBetClient is a thread-safe BookmakerClient fake used in concurrent tests.
// It counts accepted bets so concurrent tests can assert on the count without data races.
type concurrentBetClient struct {
	acceptedBets int64
}

func (c *concurrentBetClient) GetOffers(_ context.Context, _ string) ([]bookmaker.LineOffer, error) {
	return nil, nil
}
func (c *concurrentBetClient) PlaceBet(_ context.Context, _ bookmaker.BetRequest) (bookmaker.BetResponse, error) {
	atomic.AddInt64(&c.acceptedBets, 1)
	return bookmaker.BetResponse{BetID: "b1", AcceptedStake: 50, Filled: true}, nil
}

type fakeAccountManager struct {
	balance  float64
	maxStake float64
	err      error
}

func (f *fakeAccountManager) Balance(_ context.Context) (float64, error) {
	return f.balance, f.err
}
func (f *fakeAccountManager) MaxStake(_ context.Context, _, _ string) (float64, error) {
	return f.maxStake, f.err
}

func acceptedResp(stake float64) bookmaker.BetResponse {
	return bookmaker.BetResponse{BetID: "b1", AcceptedStake: stake, Filled: true}
}

// --- tests ---

func TestSafeClient_ForwardsValidBet(t *testing.T) {
	// Arrange
	inner := &fakeBetClient{resp: acceptedResp(50)}
	am := &fakeAccountManager{balance: 1000, maxStake: 100}
	c := bookmaker.NewSafeBookmakerClient(inner, am,
		bookmaker.WithSafeMaxStakeCap(100),
		bookmaker.WithSafeBalanceFloor(10),
	)

	// Act
	resp, err := c.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID: "o1", MarketID: "m1", Side: "home", RequestedStake: 50, DecimalOdds: 1.9,
	})

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.Rejected {
		t.Errorf("expected forwarded bet, got rejected: %s", resp.RejectionReason)
	}
}

func TestSafeClient_CapsStakeAtMaxStakeCap(t *testing.T) {
	// Arrange
	inner := &fakeBetClient{resp: acceptedResp(75)}
	am := &fakeAccountManager{balance: 1000, maxStake: 200}
	c := bookmaker.NewSafeBookmakerClient(inner, am,
		bookmaker.WithSafeMaxStakeCap(75),
		bookmaker.WithSafeBalanceFloor(0),
	)

	// Act
	_, err := c.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID: "o1", MarketID: "m1", Side: "home", RequestedStake: 200, DecimalOdds: 1.9,
	})

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(inner.reqs) == 0 {
		t.Fatal("expected inner to be called")
	}
	if inner.reqs[0].RequestedStake != 75 {
		t.Errorf("stake forwarded to inner: want 75, got %v", inner.reqs[0].RequestedStake)
	}
}

func TestSafeClient_RejectsWhenBalanceBelowFloor(t *testing.T) {
	// Arrange
	inner := &fakeBetClient{resp: acceptedResp(50)}
	am := &fakeAccountManager{balance: 80, maxStake: 100} // balance < floor
	c := bookmaker.NewSafeBookmakerClient(inner, am,
		bookmaker.WithSafeMaxStakeCap(100),
		bookmaker.WithSafeBalanceFloor(100),
	)

	// Act
	resp, err := c.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID: "o1", MarketID: "m1", Side: "home", RequestedStake: 50, DecimalOdds: 1.9,
	})

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !resp.Rejected {
		t.Errorf("expected rejection when balance below floor")
	}
	if len(inner.reqs) != 0 {
		t.Errorf("inner should not be called when rejected by safety check")
	}
}

func TestSafeClient_AllowsWhenBalanceAboveFloor(t *testing.T) {
	// Arrange
	inner := &fakeBetClient{resp: acceptedResp(50)}
	am := &fakeAccountManager{balance: 500, maxStake: 100}
	c := bookmaker.NewSafeBookmakerClient(inner, am,
		bookmaker.WithSafeMaxStakeCap(100),
		bookmaker.WithSafeBalanceFloor(100),
	)

	// Act
	resp, _ := c.PlaceBet(context.Background(), bookmaker.BetRequest{
		OfferID: "o1", MarketID: "m1", Side: "home", RequestedStake: 50, DecimalOdds: 1.9,
	})

	// Assert
	if resp.Rejected {
		t.Errorf("expected bet to pass when balance above floor")
	}
}

func TestSafeClient_RejectsDuplicateBetWithinTTL(t *testing.T) {
	// Arrange: first bet succeeds, second on same market+side is a duplicate
	inner := &fakeBetClient{resp: acceptedResp(50)}
	am := &fakeAccountManager{balance: 1000, maxStake: 100}
	c := bookmaker.NewSafeBookmakerClient(inner, am,
		bookmaker.WithSafeMaxStakeCap(100),
		bookmaker.WithSafeBalanceFloor(0),
		bookmaker.WithSafeDedupTTL(5*time.Minute),
	)
	req := bookmaker.BetRequest{
		OfferID: "o1", MarketID: "m1", Side: "home", RequestedStake: 50, DecimalOdds: 1.9,
	}

	// Act
	_, _ = c.PlaceBet(context.Background(), req)
	req.OfferID = "o2"
	resp, _ := c.PlaceBet(context.Background(), req)

	// Assert
	if !resp.Rejected {
		t.Errorf("expected second bet on same market+side to be rejected as duplicate")
	}
}

func TestSafeClient_AllowsAfterDedupTTLExpires(t *testing.T) {
	// Arrange: use a very short TTL, then advance past it
	calls := 0
	inner := &fakeBetClient{}
	inner.resp = bookmaker.BetResponse{BetID: "b1", AcceptedStake: 50, Filled: true}
	am := &fakeAccountManager{balance: 1000, maxStake: 100}

	now := fixedNow
	c := bookmaker.NewSafeBookmakerClient(inner, am,
		bookmaker.WithSafeMaxStakeCap(100),
		bookmaker.WithSafeBalanceFloor(0),
		bookmaker.WithSafeDedupTTL(10*time.Second),
		bookmaker.WithSafeNow(func() time.Time {
			t := now.Add(time.Duration(calls) * 15 * time.Second)
			calls++
			return t
		}),
	)
	req := bookmaker.BetRequest{
		OfferID: "o1", MarketID: "m1", Side: "home", RequestedStake: 50, DecimalOdds: 1.9,
	}

	// Act
	_, _ = c.PlaceBet(context.Background(), req)
	req.OfferID = "o2"
	resp, _ := c.PlaceBet(context.Background(), req)

	// Assert: second bet occurs 15s after first; TTL is 10s — should be allowed
	if resp.Rejected {
		t.Errorf("expected bet to be allowed after dedup TTL: %s", resp.RejectionReason)
	}
}

// TestSafeClient_ConcurrentDedupPreventsRace fires N goroutines simultaneously placing
// a bet on the same market+side. After the fix, the dedup map is atomically reserved
// before the inner call, so exactly one goroutine proceeds to the inner client.
// The race detector will catch any concurrent map read/write on the unpatched code.
func TestSafeClient_ConcurrentDedupPreventsRace(t *testing.T) {
	// Arrange
	const goroutines = 20
	inner := &concurrentBetClient{}
	am := &fakeAccountManager{balance: 1000, maxStake: 100}
	c := bookmaker.NewSafeBookmakerClient(inner, am,
		bookmaker.WithSafeMaxStakeCap(100),
		bookmaker.WithSafeBalanceFloor(0),
		bookmaker.WithSafeDedupTTL(5*time.Minute),
	)

	var wg sync.WaitGroup
	start := make(chan struct{})

	// Act: launch all goroutines, hold them at start, then release simultaneously.
	for i := range goroutines {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			<-start
			_, _ = c.PlaceBet(context.Background(), bookmaker.BetRequest{
				OfferID:        "o" + string(rune('0'+i)),
				MarketID:       "m1",
				Side:           "home",
				RequestedStake: 10,
				DecimalOdds:    1.9,
			})
		}(i)
	}
	close(start)
	wg.Wait()

	// Assert: exactly one goroutine should have reached the inner client;
	// all others must have been blocked by the dedup reservation.
	accepted := atomic.LoadInt64(&inner.acceptedBets)
	if accepted != 1 {
		t.Errorf("concurrent dedup: inner called %d times, want exactly 1", accepted)
	}
}

// compile-time check
var _ bookmaker.BookmakerClient = (*bookmaker.SafeBookmakerClient)(nil)
