package marketdata

import "time"

// BookType classifies a bookmaker by its market-making behaviour.
type BookType string

const (
	BookTypeSharp    BookType = "sharp"
	BookTypeSoft     BookType = "soft"
	BookTypeExchange BookType = "exchange"
)

// Book represents a bookmaker that offers odds.
type Book struct {
	ID   string   `json:"id"`
	Name string   `json:"name"`
	Type BookType `json:"type"`
}

// Sport identifies which sport an event belongs to.
type Sport string

const (
	SportNFL    Sport = "nfl"
	SportNBA    Sport = "nba"
	SportMLB    Sport = "mlb"
	SportNHL    Sport = "nhl"
	SportSoccer Sport = "soccer"
)

// Event represents a scheduled sporting contest.
type Event struct {
	ID       string    `json:"id"`
	Sport    Sport     `json:"sport"`
	HomeTeam string    `json:"home_team"`
	AwayTeam string    `json:"away_team"`
	StartsAt time.Time `json:"starts_at"`
	Season   string    `json:"season"`
	Week     *int      `json:"week,omitempty"` // NFL only; null for all other sports
	Venue    string    `json:"venue"`
}

// MarketType identifies the kind of bet a market represents.
type MarketType string

const (
	MarketTypeMoneyline  MarketType = "moneyline"
	MarketTypeSpread     MarketType = "spread"
	MarketTypeTotal      MarketType = "total"
	MarketTypePlayerProp MarketType = "player_prop"
)

// Market is a single wagerable outcome type for an event (e.g., moneyline, spread).
type Market struct {
	ID        string     `json:"id"`
	EventID   string     `json:"event_id"`
	Type      MarketType `json:"type"`
	CreatedAt time.Time  `json:"created_at"`
}

// Side identifies which outcome of a market a line prices.
type Side string

const (
	SideHome  Side = "home"
	SideAway  Side = "away"
	SideDraw  Side = "draw"
	SideOver  Side = "over"
	SideUnder Side = "under"
)

// Line is a single price offered by one book for one side of a market at a moment in time.
//
// RawImpliedProb is derived directly from the quoted odds and includes the bookmaker margin.
// ImpliedProb is the devigged (true market) probability, obtained by removing the margin
// across all sides in the same snapshot.
type Line struct {
	ID             string    `json:"id"`
	MarketID       string    `json:"market_id"`
	BookID         string    `json:"book_id"`
	Side           Side      `json:"side"`
	Label          string    `json:"label"`
	AmericanOdds   int       `json:"american_odds"`
	DecimalOdds    float64   `json:"decimal_odds"`
	RawImpliedProb float64   `json:"raw_implied_prob"`
	ImpliedProb    float64   `json:"implied_prob"`
	Spread         *float64  `json:"spread,omitempty"`
	Total          *float64  `json:"total,omitempty"`
	RecordedAt     time.Time `json:"recorded_at"`
	IsClosing      bool      `json:"is_closing"`
}
