package marketdata

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"
)

var _ OddsProvider = (*StaticOddsProvider)(nil)

// lineRecord is the raw line shape in a static JSON file.
// Only american_odds is required; decimal and implied probability fields are computed on load.
type lineRecord struct {
	ID           string    `json:"id"`
	MarketID     string    `json:"market_id"`
	BookID       string    `json:"book_id"`
	Side         Side      `json:"side"`
	Label        string    `json:"label"`
	AmericanOdds int       `json:"american_odds"`
	Spread       *float64  `json:"spread,omitempty"`
	Total        *float64  `json:"total,omitempty"`
	RecordedAt   time.Time `json:"recorded_at"`
	IsClosing    bool      `json:"is_closing"`
}

// staticData mirrors the top-level structure of a static odds JSON file.
type staticData struct {
	Books   []Book       `json:"books"`
	Events  []Event      `json:"events"`
	Markets []Market     `json:"markets"`
	Lines   []lineRecord `json:"lines"`
}

// StaticOddsProvider implements OddsProvider by reading a JSON file.
// On load it computes decimal odds and implied probabilities from American odds,
// then applies proportional devig within each market snapshot.
// It is intended for backtesting where no live bookmaker connection is available.
type StaticOddsProvider struct {
	events  map[string]Event
	markets map[string]Market
	lines   map[string][]Line // key: marketID
}

// NewStaticOddsProvider reads and parses the JSON file at path.
// It computes all derived odds fields and applies devig before returning.
func NewStaticOddsProvider(path string) (*StaticOddsProvider, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("reading static odds file: %w", err)
	}

	var raw staticData
	if err := json.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("parsing static odds file: %w", err)
	}

	p := &StaticOddsProvider{
		events:  make(map[string]Event, len(raw.Events)),
		markets: make(map[string]Market, len(raw.Markets)),
		lines:   make(map[string][]Line),
	}

	for _, e := range raw.Events {
		p.events[e.ID] = e
	}
	for _, m := range raw.Markets {
		p.markets[m.ID] = m
	}

	rawLines, err := convertLineRecords(raw.Lines)
	if err != nil {
		return nil, err
	}

	for _, l := range DevigLines(rawLines) {
		p.lines[l.MarketID] = append(p.lines[l.MarketID], l)
	}

	return p, nil
}

// Events returns all events matching the given sport and season.
func (p *StaticOddsProvider) Events(_ context.Context, sport Sport, season string) ([]Event, error) {
	var result []Event
	for _, e := range p.events {
		if e.Sport == sport && e.Season == season {
			result = append(result, e)
		}
	}
	return result, nil
}

// Markets returns all markets for the given event.
func (p *StaticOddsProvider) Markets(_ context.Context, eventID string) ([]Market, error) {
	var result []Market
	for _, m := range p.markets {
		if m.EventID == eventID {
			result = append(result, m)
		}
	}
	return result, nil
}

// Lines returns all lines for the given market with decimal odds and devigged probabilities set.
func (p *StaticOddsProvider) Lines(_ context.Context, marketID string) ([]Line, error) {
	src := p.lines[marketID]
	result := make([]Line, len(src))
	copy(result, src)
	return result, nil
}

func convertLineRecords(records []lineRecord) ([]Line, error) {
	lines := make([]Line, 0, len(records))
	for _, r := range records {
		decimal, err := AmericanOdds(r.AmericanOdds).ToDecimal()
		if err != nil {
			return nil, fmt.Errorf("line %q: %w", r.ID, err)
		}
		rawProb, err := decimal.ToImpliedProbability()
		if err != nil {
			return nil, fmt.Errorf("line %q: %w", r.ID, err)
		}
		lines = append(lines, Line{
			ID:             r.ID,
			MarketID:       r.MarketID,
			BookID:         r.BookID,
			Side:           r.Side,
			Label:          r.Label,
			AmericanOdds:   r.AmericanOdds,
			DecimalOdds:    float64(decimal),
			RawImpliedProb: float64(rawProb),
			Spread:         r.Spread,
			Total:          r.Total,
			RecordedAt:     r.RecordedAt,
			IsClosing:      r.IsClosing,
		})
	}
	return lines, nil
}
