package marketdata_test

import (
	"context"
	"testing"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

func TestNullOddsProvider(t *testing.T) {
	// Arrange
	var p marketdata.NullOddsProvider
	ctx := context.Background()

	t.Run("Events returns empty slice", func(t *testing.T) {
		// Act
		events, err := p.Events(ctx, marketdata.SportNFL, "2024")

		// Assert
		if err != nil {
			t.Fatalf("Events: unexpected error: %v", err)
		}
		if len(events) != 0 {
			t.Errorf("Events() count = %d, want 0", len(events))
		}
	})

	t.Run("Markets returns empty slice", func(t *testing.T) {
		// Act
		markets, err := p.Markets(ctx, "any-event")

		// Assert
		if err != nil {
			t.Fatalf("Markets: unexpected error: %v", err)
		}
		if len(markets) != 0 {
			t.Errorf("Markets() count = %d, want 0", len(markets))
		}
	})

	t.Run("Lines returns empty slice", func(t *testing.T) {
		// Act
		lines, err := p.Lines(ctx, "any-market")

		// Assert
		if err != nil {
			t.Fatalf("Lines: unexpected error: %v", err)
		}
		if len(lines) != 0 {
			t.Errorf("Lines() count = %d, want 0", len(lines))
		}
	})

	t.Run("Books returns empty slice", func(t *testing.T) {
		// Act
		books, err := p.Books(ctx)

		// Assert
		if err != nil {
			t.Fatalf("Books: unexpected error: %v", err)
		}
		if len(books) != 0 {
			t.Errorf("Books() count = %d, want 0", len(books))
		}
	})
}
