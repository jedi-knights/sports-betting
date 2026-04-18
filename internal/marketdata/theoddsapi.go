package marketdata

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"sync"
	"time"
)

var _ OddsProvider = (*TheOddsAPIProvider)(nil)

// knownBookmakers classifies US bookmakers by their market-making behaviour.
// Keys are The Odds API bookmaker identifiers.
// Bookmakers absent from this map are treated as soft by default.
var knownBookmakers = map[string]Book{
	"pinnacle":      {ID: "pinnacle", Name: "Pinnacle", Type: BookTypeSharp},
	"lowvig":        {ID: "lowvig", Name: "LowVig.ag", Type: BookTypeSharp},
	"betonlineag":   {ID: "betonlineag", Name: "BetOnline.ag", Type: BookTypeSharp},
	"bookmaker":     {ID: "bookmaker", Name: "BookMaker", Type: BookTypeSharp},
	"circa":         {ID: "circa", Name: "Circa Sports", Type: BookTypeSharp},
	"betfair_ex_us": {ID: "betfair_ex_us", Name: "Betfair Exchange", Type: BookTypeExchange},
	"draftkings":    {ID: "draftkings", Name: "DraftKings", Type: BookTypeSoft},
	"fanduel":       {ID: "fanduel", Name: "FanDuel", Type: BookTypeSoft},
	"betmgm":        {ID: "betmgm", Name: "BetMGM", Type: BookTypeSoft},
	"caesars":       {ID: "caesars", Name: "Caesars", Type: BookTypeSoft},
	"pointsbetus":   {ID: "pointsbetus", Name: "PointsBet", Type: BookTypeSoft},
	"betrivers":     {ID: "betrivers", Name: "BetRivers", Type: BookTypeSoft},
	"wynnbet":       {ID: "wynnbet", Name: "WynnBet", Type: BookTypeSoft},
	"barstool":      {ID: "barstool", Name: "Barstool", Type: BookTypeSoft},
	"hardrock":      {ID: "hardrock", Name: "Hard Rock Bet", Type: BookTypeSoft},
	"unibet_us":     {ID: "unibet_us", Name: "Unibet", Type: BookTypeSoft},
	"bet365_us":     {ID: "bet365_us", Name: "Bet365", Type: BookTypeSoft},
	"superbook":     {ID: "superbook", Name: "SuperBook", Type: BookTypeSoft},
	"espnbet":       {ID: "espnbet", Name: "ESPN BET", Type: BookTypeSoft},
	"fliff":         {ID: "fliff", Name: "Fliff", Type: BookTypeSoft},
}

// sportKeys maps our internal Sport type to The Odds API v4 sport key.
var sportKeys = map[Sport]string{
	SportNFL:    "americanfootball_nfl",
	SportNBA:    "basketball_nba",
	SportMLB:    "baseball_mlb",
	SportNHL:    "icehockey_nhl",
	SportSoccer: "soccer_epl",
}

// apiMarketTypes maps The Odds API market keys to our internal MarketType.
var apiMarketTypes = map[string]MarketType{
	"h2h":     MarketTypeMoneyline,
	"spreads": MarketTypeSpread,
	"totals":  MarketTypeTotal,
}

// oddsAPIEvent is the JSON shape returned by the The Odds API v4 odds endpoint.
type oddsAPIEvent struct {
	ID           string             `json:"id"`
	SportKey     string             `json:"sport_key"`
	CommenceTime time.Time          `json:"commence_time"`
	HomeTeam     string             `json:"home_team"`
	AwayTeam     string             `json:"away_team"`
	Bookmakers   []oddsAPIBookmaker `json:"bookmakers"`
}

type oddsAPIBookmaker struct {
	Key        string          `json:"key"`
	Title      string          `json:"title"`
	LastUpdate time.Time       `json:"last_update"`
	Markets    []oddsAPIMarket `json:"markets"`
}

type oddsAPIMarket struct {
	Key        string           `json:"key"`
	LastUpdate time.Time        `json:"last_update"`
	Outcomes   []oddsAPIOutcome `json:"outcomes"`
}

type oddsAPIOutcome struct {
	Name  string   `json:"name"`
	Price int      `json:"price"`
	Point *float64 `json:"point,omitempty"`
}

// TheOddsAPIProvider implements OddsProvider by fetching live odds from The Odds API v4.
// On each call to Events, it refreshes an internal cache of events, markets, and lines
// by fetching the combined odds endpoint. Markets and Lines serve from that cache.
// Safe for concurrent use.
type TheOddsAPIProvider struct {
	apiKey     string
	baseURL    string
	httpClient *http.Client

	mu           sync.RWMutex
	books        []Book
	events       map[string]Event
	eventMarkets map[string][]string // eventID → []marketID (ordered, deduplicated)
	markets      map[string]Market   // marketID → Market
	lines        map[string][]Line   // marketID → []Line
}

// Option configures a TheOddsAPIProvider.
type Option func(*TheOddsAPIProvider)

// WithBaseURL overrides the API base URL. Intended for testing.
func WithBaseURL(baseURL string) Option {
	return func(p *TheOddsAPIProvider) {
		p.baseURL = baseURL
	}
}

// NewTheOddsAPIProvider creates a provider backed by The Odds API v4.
func NewTheOddsAPIProvider(apiKey string, opts ...Option) *TheOddsAPIProvider {
	p := &TheOddsAPIProvider{
		apiKey:       apiKey,
		baseURL:      "https://api.the-odds-api.com",
		httpClient:   &http.Client{Timeout: 10 * time.Second},
		events:       make(map[string]Event),
		eventMarkets: make(map[string][]string),
		markets:      make(map[string]Market),
		lines:        make(map[string][]Line),
	}
	for _, o := range opts {
		o(p)
	}
	return p
}

// Events fetches upcoming events for the given sport from The Odds API, refreshes the
// internal cache, then returns events whose season year matches the season argument.
func (p *TheOddsAPIProvider) Events(ctx context.Context, sport Sport, season string) ([]Event, error) {
	sportKey, ok := sportKeys[sport]
	if !ok {
		return nil, fmt.Errorf("unsupported sport: %s", sport)
	}
	if err := p.refresh(ctx, sport, sportKey); err != nil {
		return nil, err
	}
	p.mu.RLock()
	defer p.mu.RUnlock()
	var result []Event
	for _, e := range p.events {
		if e.Season == season {
			result = append(result, e)
		}
	}
	return result, nil
}

// Markets returns all markets for the given event from the cache.
// Events must be fetched first to populate the cache.
func (p *TheOddsAPIProvider) Markets(_ context.Context, eventID string) ([]Market, error) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	ids := p.eventMarkets[eventID]
	result := make([]Market, 0, len(ids))
	for _, id := range ids {
		if m, ok := p.markets[id]; ok {
			result = append(result, m)
		}
	}
	return result, nil
}

// Books returns the bookmakers seen in the last refresh, classified by type.
// Events must be fetched first to populate the cache.
func (p *TheOddsAPIProvider) Books(_ context.Context) ([]Book, error) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	result := make([]Book, len(p.books))
	copy(result, p.books)
	return result, nil
}

// Lines returns all lines for the given market from the cache.
// Events must be fetched first to populate the cache.
func (p *TheOddsAPIProvider) Lines(_ context.Context, marketID string) ([]Line, error) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	src := p.lines[marketID]
	result := make([]Line, len(src))
	copy(result, src)
	return result, nil
}

// refresh fetches the latest odds for the given sport key and rebuilds the cache atomically.
func (p *TheOddsAPIProvider) refresh(ctx context.Context, sport Sport, sportKey string) error {
	endpoint := fmt.Sprintf("%s/v4/sports/%s/odds", p.baseURL, sportKey)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return fmt.Errorf("building request: %w", err)
	}
	q := url.Values{}
	q.Set("apiKey", p.apiKey)
	q.Set("regions", "us")
	q.Set("markets", "h2h,spreads,totals")
	q.Set("oddsFormat", "american")
	req.URL.RawQuery = q.Encode()

	resp, err := p.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("fetching odds: %w", err)
	}
	defer func() { _ = resp.Body.Close() }()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("odds API responded with status %d", resp.StatusCode)
	}

	var apiEvents []oddsAPIEvent
	if err := json.NewDecoder(resp.Body).Decode(&apiEvents); err != nil {
		return fmt.Errorf("decoding odds response: %w", err)
	}

	events := make(map[string]Event, len(apiEvents))
	eventMarkets := make(map[string][]string)
	markets := make(map[string]Market)
	seenBooks := make(map[string]Book)
	var allLines []Line

	for _, ae := range apiEvents {
		season := fmt.Sprintf("%d", ae.CommenceTime.Year())
		events[ae.ID] = Event{
			ID:       ae.ID,
			Sport:    sport,
			HomeTeam: ae.HomeTeam,
			AwayTeam: ae.AwayTeam,
			StartsAt: ae.CommenceTime,
			Season:   season,
		}

		for _, bm := range ae.Bookmakers {
			if _, seen := seenBooks[bm.Key]; !seen {
				if known, ok := knownBookmakers[bm.Key]; ok {
					seenBooks[bm.Key] = known
				} else {
					seenBooks[bm.Key] = Book{ID: bm.Key, Name: bm.Title, Type: BookTypeSoft}
				}
			}
			for _, mkt := range bm.Markets {
				marketType, ok := apiMarketTypes[mkt.Key]
				if !ok {
					continue
				}
				marketID := ae.ID + "_" + mkt.Key

				// One Market record per (event, market type) — shared across bookmakers.
				if _, exists := markets[marketID]; !exists {
					markets[marketID] = Market{
						ID:        marketID,
						EventID:   ae.ID,
						Type:      marketType,
						CreatedAt: mkt.LastUpdate,
					}
					eventMarkets[ae.ID] = append(eventMarkets[ae.ID], marketID)
				}

				for _, outcome := range mkt.Outcomes {
					side := outcomeNameToSide(outcome.Name, ae.HomeTeam, ae.AwayTeam)
					lineID := marketID + "_" + bm.Key + "_" + string(side)
					decimal, err := AmericanOdds(outcome.Price).ToDecimal()
					if err != nil {
						continue
					}
					rawProb, err := decimal.ToImpliedProbability()
					if err != nil {
						continue
					}
					line := Line{
						ID:             lineID,
						MarketID:       marketID,
						BookID:         bm.Key,
						Side:           side,
						Label:          outcome.Name,
						AmericanOdds:   outcome.Price,
						DecimalOdds:    float64(decimal),
						RawImpliedProb: float64(rawProb),
						RecordedAt:     mkt.LastUpdate,
					}
					if marketType == MarketTypeSpread {
						line.Spread = outcome.Point
					}
					if marketType == MarketTypeTotal {
						line.Total = outcome.Point
					}
					allLines = append(allLines, line)
				}
			}
		}
	}

	devigged := DevigLines(allLines)
	linesByMarket := make(map[string][]Line, len(markets))
	for _, l := range devigged {
		linesByMarket[l.MarketID] = append(linesByMarket[l.MarketID], l)
	}

	books := make([]Book, 0, len(seenBooks))
	for _, b := range seenBooks {
		books = append(books, b)
	}

	p.mu.Lock()
	p.books = books
	p.events = events
	p.eventMarkets = eventMarkets
	p.markets = markets
	p.lines = linesByMarket
	p.mu.Unlock()

	return nil
}

// outcomeNameToSide maps an outcome name to a Side using the event's team names.
func outcomeNameToSide(name, homeTeam, awayTeam string) Side {
	switch name {
	case homeTeam:
		return SideHome
	case awayTeam:
		return SideAway
	case "Over":
		return SideOver
	case "Under":
		return SideUnder
	case "Draw":
		return SideDraw
	default:
		return Side(name)
	}
}
