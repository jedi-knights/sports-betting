// Command paper-trade evaluates lines written by market-data into the shared LineStore,
// runs them through a SimulatedBookmakerClient, records paper bets, and exposes a REST
// API for monitoring open positions and performance.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/jedi-knights/sports-betting/internal/bettracking"
	"github.com/jedi-knights/sports-betting/internal/bookmaker"
	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	addr := envOr("ADDR", ":8080")
	pollInterval := durationEnv("POLL_INTERVAL_SECONDS", 60)

	lineStore, err := buildLineStore(ctx, logger)
	if err != nil {
		logger.Error("building line store", "error", err)
		os.Exit(1)
	}
	if closer, ok := lineStore.(interface{ Close() }); ok {
		defer closer.Close()
	}

	betStore := bettracking.NewMemoryBetStore()
	book := bookmaker.NewSimulatedBookmakerClient(
		bookmaker.WithMargin(0.05),
		bookmaker.WithMaxStake(100),
		bookmaker.WithOfferTTL(30*time.Second),
	)

	svc := &paperTradeService{
		logger:    logger,
		lineStore: lineStore,
		betStore:  betStore,
		book:      book,
	}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /paper/bets", svc.handleGetBets)
	mux.HandleFunc("GET /paper/performance", svc.handleGetPerformance)

	server := &http.Server{
		Addr:         addr,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	go func() {
		logger.Info("paper-trade service listening", "addr", addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("HTTP server error", "error", err)
		}
	}()

	ticker := time.NewTicker(pollInterval)
	defer ticker.Stop()

	svc.poll(ctx)
	for {
		select {
		case <-ticker.C:
			svc.poll(ctx)
		case <-ctx.Done():
			logger.Info("paper-trade service shutting down")
			shutCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			_ = server.Shutdown(shutCtx)
			return
		}
	}
}

type paperTradeService struct {
	logger    *slog.Logger
	lineStore marketdata.LineStore
	betStore  bettracking.BetStore
	book      *bookmaker.SimulatedBookmakerClient
}

func (s *paperTradeService) poll(ctx context.Context) {
	marketIDs, err := s.lineStore.Markets(ctx)
	if err != nil {
		s.logger.Error("fetching markets from line store", "error", err)
		return
	}
	for _, marketID := range marketIDs {
		lines, err := s.lineStore.Lines(ctx, marketID)
		if err != nil {
			s.logger.Error("fetching lines", "market_id", marketID, "error", err)
			continue
		}
		if len(lines) == 0 {
			continue
		}
		s.evaluateMarket(ctx, marketID, lines)
	}
	s.logger.Info("paper trade poll complete", "markets", len(marketIDs))
}

func (s *paperTradeService) evaluateMarket(ctx context.Context, marketID string, lines []marketdata.Line) {
	// EventID is denormalized onto Line by market-data; fall back to marketID if absent.
	eventID := marketID
	if len(lines) > 0 && lines[0].EventID != "" {
		eventID = lines[0].EventID
	}

	for _, line := range lines {
		s.book.SetMarket(marketID, string(line.Side), line.ImpliedProb)
	}

	offers, err := s.book.GetOffers(ctx, marketID)
	if err != nil {
		s.logger.Error("getting offers", "market_id", marketID, "error", err)
		return
	}
	for _, offer := range offers {
		// Only bet when the offered decimal odds imply >5% edge over the true probability.
		trueImplied := 1.0 / offer.DecimalOdds * (1 + 0.05)
		if trueImplied < 0.5 {
			continue
		}
		resp, err := s.book.PlaceBet(ctx, bookmaker.BetRequest{
			OfferID:        offer.OfferID,
			MarketID:       offer.MarketID,
			Side:           offer.Side,
			RequestedStake: 10.0,
			DecimalOdds:    offer.DecimalOdds,
		})
		if err != nil || resp.Rejected {
			continue
		}
		bet := bettracking.Bet{
			ID:          resp.BetID,
			EventID:     eventID,
			MarketID:    marketID,
			Side:        offer.Side,
			Stake:       resp.AcceptedStake,
			DecimalOdds: resp.DecimalOdds,
			PlacedAt:    time.Now(),
			Status:      bettracking.BetStatusOpen,
		}
		if err := s.betStore.Save(bet); err != nil {
			s.logger.Error("saving bet", "bet_id", bet.ID, "error", err)
		}
	}
}

func (s *paperTradeService) handleGetBets(w http.ResponseWriter, _ *http.Request) {
	bets, err := s.betStore.FindAll()
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(bets); err != nil {
		s.logger.Error("encoding bets response", "error", err)
	}
}

func (s *paperTradeService) handleGetPerformance(w http.ResponseWriter, _ *http.Request) {
	bets, err := s.betStore.FindAll()
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	results := make([]bettracking.BetResult, 0, len(bets))
	for _, b := range bets {
		results = append(results, bettracking.NewBetResult(b))
	}
	report := bettracking.ComputePerformanceReport(results)
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(report); err != nil {
		s.logger.Error("encoding performance response", "error", err)
	}
}

func buildLineStore(ctx context.Context, logger *slog.Logger) (marketdata.LineStore, error) {
	if dsn := os.Getenv("DATABASE_URL"); dsn != "" {
		store, err := marketdata.NewPostgresLineStore(ctx, dsn)
		if err != nil {
			return nil, fmt.Errorf("connecting to postgres: %w", err)
		}
		logger.Info("using postgres line store")
		return store, nil
	}
	logger.Warn("DATABASE_URL not set — using in-memory line store (paper bets will not survive restarts)")
	return marketdata.NewMemoryLineStore(), nil
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func durationEnv(key string, fallbackSeconds int) time.Duration {
	if v := os.Getenv(key); v != "" {
		if d, err := time.ParseDuration(v + "s"); err == nil {
			return d
		}
	}
	return time.Duration(fallbackSeconds) * time.Second
}
