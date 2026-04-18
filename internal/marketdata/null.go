package marketdata

import "context"

var _ OddsProvider = NullOddsProvider{}

// NullOddsProvider is an OddsProvider that returns no events, markets, lines, or books.
// It is used as a stand-in when no data source is configured so services can start
// without a data file or API key, and simply produce empty results on each poll cycle.
type NullOddsProvider struct{}

// Events implements OddsProvider. It always returns an empty slice.
func (NullOddsProvider) Events(_ context.Context, _ Sport, _ string) ([]Event, error) {
	return nil, nil
}

// Markets implements OddsProvider. It always returns an empty slice.
func (NullOddsProvider) Markets(_ context.Context, _ string) ([]Market, error) {
	return nil, nil
}

// Lines implements OddsProvider. It always returns an empty slice.
func (NullOddsProvider) Lines(_ context.Context, _ string) ([]Line, error) {
	return nil, nil
}

// Books implements OddsProvider. It always returns an empty slice.
func (NullOddsProvider) Books(_ context.Context) ([]Book, error) {
	return nil, nil
}
