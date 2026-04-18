package marketdata

import "context"

// OddsProvider fetches events, markets, and lines from an external source.
// Implementations include StaticOddsProvider for backtesting and live bookmaker
// clients for paper trading and live execution.
type OddsProvider interface {
	Events(ctx context.Context, sport Sport, season string) ([]Event, error)
	Markets(ctx context.Context, eventID string) ([]Market, error)
	Lines(ctx context.Context, marketID string) ([]Line, error)
}

// LineStore persists and queries the line history for a set of markets.
// Implementations include the in-memory store for testing and PostgreSQL for running services.
type LineStore interface {
	SaveLines(ctx context.Context, lines []Line) error
	Lines(ctx context.Context, marketID string) ([]Line, error)
	ClosingLine(ctx context.Context, marketID string, side Side) (*Line, error)
}
