package marketdata_test

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

// TestPostgresLineStore runs against a real PostgreSQL instance.
// Set TEST_DATABASE_URL to a valid connection string to enable these tests.
// Example: TEST_DATABASE_URL=postgres://sportsbetting:changeme@localhost:5433/sportsbetting?sslmode=disable
func TestPostgresLineStore(t *testing.T) {
	connStr := os.Getenv("TEST_DATABASE_URL")
	if connStr == "" {
		t.Skip("TEST_DATABASE_URL not set — skipping Postgres integration tests")
	}

	ctx := context.Background()
	store, err := marketdata.NewPostgresLineStore(ctx, connStr)
	if err != nil {
		t.Fatalf("NewPostgresLineStore: %v", err)
	}
	defer store.Close()

	// Clean state before each run so tests are repeatable.
	if err := store.Truncate(ctx); err != nil {
		t.Fatalf("Truncate: %v", err)
	}

	now := time.Now().UTC().Truncate(time.Microsecond) // Postgres stores microsecond precision
	lines := []marketdata.Line{
		{ID: "pg-l1", EventID: "ev1", MarketID: "pg-m1", BookID: "b1", Side: marketdata.SideHome, AmericanOdds: -200, DecimalOdds: 1.5, RawImpliedProb: 0.6, ImpliedProb: 0.5625, IsClosing: false, RecordedAt: now},
		{ID: "pg-l2", EventID: "ev1", MarketID: "pg-m1", BookID: "b1", Side: marketdata.SideAway, AmericanOdds: 160, DecimalOdds: 2.6, RawImpliedProb: 0.385, ImpliedProb: 0.4375, IsClosing: false, RecordedAt: now},
		{ID: "pg-l3", EventID: "ev1", MarketID: "pg-m1", BookID: "b1", Side: marketdata.SideHome, AmericanOdds: -190, DecimalOdds: 1.526, RawImpliedProb: 0.655, ImpliedProb: 0.5625, IsClosing: true, RecordedAt: now.Add(time.Hour)},
	}

	if err := store.SaveLines(ctx, lines); err != nil {
		t.Fatalf("SaveLines: %v", err)
	}

	t.Run("retrieves all lines for market", func(t *testing.T) {
		// Act
		got, err := store.Lines(ctx, "pg-m1")

		// Assert
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		if len(got) != 3 {
			t.Errorf("Lines() count = %d, want 3", len(got))
		}
	})

	t.Run("returns empty for unknown market", func(t *testing.T) {
		// Act
		got, err := store.Lines(ctx, "unknown-market")

		// Assert
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		if len(got) != 0 {
			t.Errorf("Lines() count = %d, want 0", len(got))
		}
	})

	t.Run("finds closing line", func(t *testing.T) {
		// Act
		got, err := store.ClosingLine(ctx, "pg-m1", marketdata.SideHome)

		// Assert
		if err != nil {
			t.Fatalf("ClosingLine: %v", err)
		}
		if got == nil {
			t.Fatal("ClosingLine() = nil, want a line")
		}
		if got.ID != "pg-l3" {
			t.Errorf("ClosingLine().ID = %q, want %q", got.ID, "pg-l3")
		}
	})

	t.Run("returns nil for side with no closing line", func(t *testing.T) {
		// Act
		got, err := store.ClosingLine(ctx, "pg-m1", marketdata.SideAway)

		// Assert
		if err != nil {
			t.Fatalf("ClosingLine: %v", err)
		}
		if got != nil {
			t.Errorf("ClosingLine() = %v, want nil", got)
		}
	})

	t.Run("Markets returns distinct market IDs", func(t *testing.T) {
		// Arrange — add a second market
		extraLines := []marketdata.Line{
			{ID: "pg-l4", EventID: "ev2", MarketID: "pg-m2", BookID: "b1", Side: marketdata.SideHome, AmericanOdds: -110, DecimalOdds: 1.9, RawImpliedProb: 0.524, ImpliedProb: 0.5, RecordedAt: now},
		}
		if err := store.SaveLines(ctx, extraLines); err != nil {
			t.Fatalf("SaveLines extra: %v", err)
		}

		// Act
		markets, err := store.Markets(ctx)

		// Assert
		if err != nil {
			t.Fatalf("Markets: %v", err)
		}
		if len(markets) != 2 {
			t.Errorf("Markets() count = %d, want 2", len(markets))
		}
	})

	t.Run("SaveLines is idempotent — upsert on ID", func(t *testing.T) {
		// Arrange — resave same ID with updated odds
		updated := []marketdata.Line{
			{ID: "pg-l1", EventID: "ev1", MarketID: "pg-m1", BookID: "b1", Side: marketdata.SideHome, AmericanOdds: -210, DecimalOdds: 1.476, RawImpliedProb: 0.677, ImpliedProb: 0.57, IsClosing: false, RecordedAt: now},
		}

		// Act
		if err := store.SaveLines(ctx, updated); err != nil {
			t.Fatalf("SaveLines upsert: %v", err)
		}

		// Assert — still 3 rows in pg-m1, odds updated
		got, err := store.Lines(ctx, "pg-m1")
		if err != nil {
			t.Fatalf("Lines after upsert: %v", err)
		}
		if len(got) != 3 {
			t.Errorf("Lines() after upsert count = %d, want 3", len(got))
		}
		for _, l := range got {
			if l.ID == "pg-l1" && l.AmericanOdds != -210 {
				t.Errorf("pg-l1 AmericanOdds = %d, want -210 after upsert", l.AmericanOdds)
			}
		}
	})
}
