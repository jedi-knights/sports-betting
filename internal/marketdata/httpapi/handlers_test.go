package httpapi_test

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/httpapi"
)

func seedStore(t *testing.T, lines []marketdata.Line) marketdata.LineStore {
	t.Helper()
	store := marketdata.NewMemoryLineStore()
	if err := store.SaveLines(context.Background(), lines); err != nil {
		t.Fatalf("seed: %v", err)
	}
	return store
}

func TestHandleGetMarkets(t *testing.T) {
	ts := time.Now()
	store := seedStore(t, []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts},
		{ID: "l2", MarketID: "m2", BookID: "b1", Side: marketdata.SideAway, RecordedAt: ts},
	})

	h := httpapi.New(store)
	req := httptest.NewRequest(http.MethodGet, "/markets", nil)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("status %d, want 200", w.Code)
	}
	var ids []string
	if err := json.NewDecoder(w.Body).Decode(&ids); err != nil {
		t.Fatalf("decoding response: %v", err)
	}
	if len(ids) != 2 {
		t.Fatalf("got %d market IDs, want 2", len(ids))
	}
}

func TestHandleGetMarkets_Empty(t *testing.T) {
	h := httpapi.New(marketdata.NewMemoryLineStore())
	req := httptest.NewRequest(http.MethodGet, "/markets", nil)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("status %d, want 200", w.Code)
	}
	var ids []string
	if err := json.NewDecoder(w.Body).Decode(&ids); err != nil {
		t.Fatalf("decoding response: %v", err)
	}
	if ids == nil {
		t.Fatal("expected empty slice, got null")
	}
}

func TestHandleGetLines(t *testing.T) {
	ts := time.Now()
	store := seedStore(t, []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts},
		{ID: "l2", MarketID: "m1", BookID: "b2", Side: marketdata.SideAway, RecordedAt: ts},
	})

	h := httpapi.New(store)
	req := httptest.NewRequest(http.MethodGet, "/markets/m1/lines", nil)
	req.SetPathValue("id", "m1")
	w := httptest.NewRecorder()
	h.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("status %d, want 200", w.Code)
	}
	var lines []marketdata.Line
	if err := json.NewDecoder(w.Body).Decode(&lines); err != nil {
		t.Fatalf("decoding response: %v", err)
	}
	if len(lines) != 2 {
		t.Fatalf("got %d lines, want 2", len(lines))
	}
}

func TestHandleGetLines_UnknownMarket(t *testing.T) {
	h := httpapi.New(marketdata.NewMemoryLineStore())
	req := httptest.NewRequest(http.MethodGet, "/markets/unknown/lines", nil)
	req.SetPathValue("id", "unknown")
	w := httptest.NewRecorder()
	h.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("status %d, want 200", w.Code)
	}
	var lines []marketdata.Line
	if err := json.NewDecoder(w.Body).Decode(&lines); err != nil {
		t.Fatalf("decoding response: %v", err)
	}
	if lines == nil {
		t.Fatal("expected empty slice, got null")
	}
}
