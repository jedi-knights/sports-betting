// Package httpapi provides the REST handlers for the market-data service.
// Routes follow REST conventions: plural nouns, no verbs in URIs.
package httpapi

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

// Handler is an http.Handler that serves the market-data REST API.
type Handler struct {
	store  marketdata.LineStore
	mux    *http.ServeMux
	logger *slog.Logger
}

// New returns a Handler wired to the given LineStore.
func New(store marketdata.LineStore) *Handler {
	h := &Handler{
		store:  store,
		mux:    http.NewServeMux(),
		logger: slog.Default(),
	}
	h.mux.HandleFunc("GET /markets", h.handleGetMarkets)
	h.mux.HandleFunc("GET /markets/{id}/lines", h.handleGetLines)
	return h
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	h.mux.ServeHTTP(w, r)
}

// handleGetMarkets returns the distinct set of market IDs that have at least one line.
func (h *Handler) handleGetMarkets(w http.ResponseWriter, r *http.Request) {
	ids, err := h.store.Markets(r.Context())
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	if ids == nil {
		ids = []string{}
	}
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(ids); err != nil {
		h.logger.Error("encoding markets response", "error", err)
	}
}

// handleGetLines returns all stored lines for the market identified by {id}.
func (h *Handler) handleGetLines(w http.ResponseWriter, r *http.Request) {
	marketID := r.PathValue("id")
	lines, err := h.store.Lines(r.Context(), marketID)
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	if lines == nil {
		lines = []marketdata.Line{}
	}
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(lines); err != nil {
		h.logger.Error("encoding lines response", "error", err)
	}
}
