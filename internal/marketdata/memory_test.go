package marketdata_test

import (
	"context"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

func TestMemoryLineStore(t *testing.T) {
	ctx := context.Background()
	store := marketdata.NewMemoryLineStore()

	now := time.Now()
	lines := []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, IsClosing: false, RecordedAt: now},
		{ID: "l2", MarketID: "m1", BookID: "b1", Side: marketdata.SideAway, IsClosing: false, RecordedAt: now},
		{ID: "l3", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, IsClosing: true, RecordedAt: now.Add(time.Hour)},
	}

	if err := store.SaveLines(ctx, lines); err != nil {
		t.Fatalf("SaveLines: %v", err)
	}

	t.Run("retrieves all lines for market", func(t *testing.T) {
		got, err := store.Lines(ctx, "m1")
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		if len(got) != 3 {
			t.Errorf("Lines() count = %d, want 3", len(got))
		}
	})

	t.Run("returns empty slice for unknown market", func(t *testing.T) {
		got, err := store.Lines(ctx, "unknown")
		if err != nil {
			t.Fatalf("Lines: %v", err)
		}
		if len(got) != 0 {
			t.Errorf("Lines() count = %d, want 0", len(got))
		}
	})

	t.Run("finds closing line", func(t *testing.T) {
		got, err := store.ClosingLine(ctx, "m1", marketdata.SideHome)
		if err != nil {
			t.Fatalf("ClosingLine: %v", err)
		}
		if got == nil {
			t.Fatal("ClosingLine() = nil, want a line")
		}
		if got.ID != "l3" {
			t.Errorf("ClosingLine().ID = %q, want %q", got.ID, "l3")
		}
	})

	t.Run("returns nil for side with no closing line", func(t *testing.T) {
		got, err := store.ClosingLine(ctx, "m1", marketdata.SideAway)
		if err != nil {
			t.Fatalf("ClosingLine: %v", err)
		}
		if got != nil {
			t.Errorf("ClosingLine() = %v, want nil", got)
		}
	})

	t.Run("returns nil for unknown market", func(t *testing.T) {
		got, err := store.ClosingLine(ctx, "unknown", marketdata.SideHome)
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
			{ID: "l4", MarketID: "m2", BookID: "b1", Side: marketdata.SideHome, RecordedAt: now},
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

	t.Run("Lines returns a copy not a reference", func(t *testing.T) {
		got, _ := store.Lines(ctx, "m1")
		got[0].Label = "mutated"
		refetch, _ := store.Lines(ctx, "m1")
		if refetch[0].Label == "mutated" {
			t.Error("Lines() returned a reference to internal state")
		}
	})
}
