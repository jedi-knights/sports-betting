package marketdata

import "context"

// OddsProvider fetches events, markets, lines, and book metadata from an external source.
// Implementations include StaticOddsProvider for backtesting and live bookmaker
// clients for paper trading and live execution.
type OddsProvider interface {
	Events(ctx context.Context, sport Sport, season string) ([]Event, error)
	Markets(ctx context.Context, eventID string) ([]Market, error)
	Lines(ctx context.Context, marketID string) ([]Line, error)
	// Books returns the set of bookmakers known to this provider, with their
	// type classification (sharp, soft, exchange). Used for CLV calculations
	// that require sharp-book closing prices.
	Books(ctx context.Context) ([]Book, error)
}

// LineStore persists and queries the line history for a set of markets.
// Implementations include the in-memory store for testing and PostgreSQL for running services.
type LineStore interface {
	SaveLines(ctx context.Context, lines []Line) error
	Lines(ctx context.Context, marketID string) ([]Line, error)
	ClosingLine(ctx context.Context, marketID string, side Side) (*Line, error)
	// Markets returns the distinct set of market IDs that have at least one saved line.
	// It is used by consumers (e.g., paper-trade) to discover what to evaluate without
	// needing their own OddsProvider.
	Markets(ctx context.Context) ([]string, error)
}
