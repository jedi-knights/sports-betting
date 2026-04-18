package bookmaker

import (
	"context"
	"fmt"
	"math"
	"sync"
	"time"
)

// Option configures a SimulatedBookmakerClient.
type Option func(*SimulatedBookmakerClient)

// WithMargin sets the fractional overround applied to all offered odds.
// E.g., WithMargin(0.05) means a 5% bookmaker margin.
func WithMargin(m float64) Option {
	return func(c *SimulatedBookmakerClient) { c.margin = m }
}

// WithMaxStake sets the initial maximum accepted stake per bet.
func WithMaxStake(s float64) Option {
	return func(c *SimulatedBookmakerClient) { c.maxStake = s }
}

// WithMaxStakeFloor sets the reduced maximum stake applied after the win limit is hit.
func WithMaxStakeFloor(f float64) Option {
	return func(c *SimulatedBookmakerClient) { c.maxStakeFloor = f }
}

// WithWinLimit sets how many consecutive recorded wins trigger account limiting.
func WithWinLimit(n int) Option {
	return func(c *SimulatedBookmakerClient) { c.winLimitN = n }
}

// WithOfferTTL sets how long each offer remains valid after being issued.
func WithOfferTTL(d time.Duration) Option {
	return func(c *SimulatedBookmakerClient) { c.offerTTL = d }
}

// WithLiquidity sets the virtual liquidity used to compute line movement.
// Higher values mean less movement per unit staked.
func WithLiquidity(l float64) Option {
	return func(c *SimulatedBookmakerClient) { c.liquidity = l }
}

// WithOddsMoveTolerance sets the maximum decimal-odds difference between the
// offered price and the current price before a bet is rejected as stale.
func WithOddsMoveTolerance(t float64) Option {
	return func(c *SimulatedBookmakerClient) { c.oddsMoveTol = t }
}

// WithNow injects a clock function, enabling deterministic tests.
func WithNow(f func() time.Time) Option {
	return func(c *SimulatedBookmakerClient) { c.now = f }
}

type marketKey struct {
	marketID string
	side     string
}

type storedOffer struct {
	LineOffer
	oddsAtCreation float64
}

// SimulatedBookmakerClient is a realistic bookmaker simulation for paper trading.
//
// Behaviour modelled:
//   - Margin applied uniformly to all offered odds.
//   - Offers expire after a configurable TTL.
//   - Bets against stale quotes (odds drifted past tolerance) are rejected.
//   - Stakes larger than maxStake are partially filled.
//   - Accepted bets move the line proportionally to stake / (stake + liquidity).
//   - After winLimitN recorded wins, maxStake drops to maxStakeFloor.
type SimulatedBookmakerClient struct {
	mu sync.Mutex

	margin        float64
	maxStake      float64
	maxStakeFloor float64
	winLimitN     int
	offerTTL      time.Duration
	liquidity     float64
	oddsMoveTol   float64

	// trueProbs holds the current true implied probability per market/side.
	// Line movement updates these values.
	trueProbs map[marketKey]float64
	// offers holds all open (not yet expired) offers indexed by offerID.
	offers     map[string]storedOffer
	winCount   int
	betCounter int
	now        func() time.Time
}

// NewSimulatedBookmakerClient creates a SimulatedBookmakerClient with sensible defaults.
func NewSimulatedBookmakerClient(opts ...Option) *SimulatedBookmakerClient {
	c := &SimulatedBookmakerClient{
		margin:        0.05,
		maxStake:      100,
		maxStakeFloor: 10,
		winLimitN:     10,
		offerTTL:      30 * time.Second,
		liquidity:     500,
		oddsMoveTol:   0.02,
		trueProbs:     make(map[marketKey]float64),
		offers:        make(map[string]storedOffer),
		now:           time.Now,
	}
	for _, o := range opts {
		o(c)
	}
	return c
}

// SetMarket registers a market side with its true (devigged) implied probability.
// Call this before GetOffers to make the market available.
func (c *SimulatedBookmakerClient) SetMarket(marketID, side string, trueProb float64) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.trueProbs[marketKey{marketID, side}] = trueProb
}

// SetNow replaces the clock function at runtime, useful for advancing time in tests.
func (c *SimulatedBookmakerClient) SetNow(f func() time.Time) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.now = f
}

// RecordWin increments the win counter. Call this when a paper bet is settled as won.
// Once winLimitN wins accumulate, maxStake is reduced to maxStakeFloor.
func (c *SimulatedBookmakerClient) RecordWin() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.winCount++
	if c.winLimitN > 0 && c.winCount >= c.winLimitN {
		c.maxStake = c.maxStakeFloor
	}
}

// GetOffers returns current line offers for all configured sides of the given market.
// Each call generates new offers with fresh expiry timestamps.
func (c *SimulatedBookmakerClient) GetOffers(_ context.Context, marketID string) ([]LineOffer, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := c.now()
	var result []LineOffer

	for k, trueProb := range c.trueProbs {
		if k.marketID != marketID {
			continue
		}
		offeredOdds := c.oddsForProb(trueProb)
		c.betCounter++
		offerID := fmt.Sprintf("offer-%s-%s-%d", marketID, k.side, c.betCounter)
		offer := LineOffer{
			OfferID:     offerID,
			MarketID:    marketID,
			Side:        k.side,
			DecimalOdds: offeredOdds,
			MaxStake:    c.maxStake,
			ExpiresAt:   now.Add(c.offerTTL),
		}
		c.offers[offerID] = storedOffer{LineOffer: offer, oddsAtCreation: offeredOdds}
		result = append(result, offer)
	}
	return result, nil
}

// PlaceBet attempts to fill a bet against a stored offer.
func (c *SimulatedBookmakerClient) PlaceBet(_ context.Context, req BetRequest) (BetResponse, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	stored, ok := c.offers[req.OfferID]
	if !ok {
		return BetResponse{Rejected: true, RejectionReason: "offer not found"}, nil
	}

	// Reject if expired.
	if c.now().After(stored.ExpiresAt) {
		delete(c.offers, req.OfferID)
		return BetResponse{Rejected: true, RejectionReason: "offer expired"}, nil
	}

	// Reject if the client's quoted odds are too far from the current offer odds.
	if math.Abs(req.DecimalOdds-stored.oddsAtCreation) > c.oddsMoveTol {
		return BetResponse{Rejected: true, RejectionReason: "odds moved"}, nil
	}

	// Partial fill: cap at current maxStake.
	accepted := req.RequestedStake
	if accepted > c.maxStake {
		accepted = c.maxStake
	}

	// Apply line movement: winning-side implied prob increases proportionally to stake.
	key := marketKey{req.MarketID, req.Side}
	if prob, found := c.trueProbs[key]; found {
		delta := accepted / (accepted + c.liquidity)
		c.trueProbs[key] = math.Min(prob+delta, 0.999)
	}

	// Consume the offer so it cannot be re-used.
	delete(c.offers, req.OfferID)

	c.betCounter++
	return BetResponse{
		BetID:         fmt.Sprintf("bet-%d", c.betCounter),
		AcceptedStake: accepted,
		DecimalOdds:   stored.DecimalOdds,
		Filled:        accepted == req.RequestedStake,
	}, nil
}

// oddsForProb converts a true implied probability to offered decimal odds after applying margin.
// offered implied prob = trueProb * (1 + margin) → decimal = 1 / offeredImplied.
func (c *SimulatedBookmakerClient) oddsForProb(trueProb float64) float64 {
	offeredImplied := trueProb * (1.0 + c.margin)
	if offeredImplied <= 0 {
		return 1.0
	}
	return 1.0 / offeredImplied
}
