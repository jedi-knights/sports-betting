// Command paper-trade runs the full betting pipeline against a SimulatedBookmakerClient,
// records paper bets, and exposes a REST API for monitoring open positions and performance.
package main

import (
	"context"
	"encoding/json"
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

	sport := marketdata.Sport(envOr("SPORT", "nfl"))
	season := envOr("SEASON", "2024")
	dataPath := envOr("DATA_PATH", "/data/odds.csv")
	addr := envOr("ADDR", ":8080")
	pollInterval := durationEnv("POLL_INTERVAL_SECONDS", 60)

	provider, err := marketdata.NewStaticOddsProvider(dataPath)
	if err != nil {
		logger.Error("loading odds provider", "path", dataPath, "error", err)
		os.Exit(1)
	}

	store := marketdata.NewMemoryLineStore()
	betStore := bettracking.NewMemoryBetStore()
	book := bookmaker.NewSimulatedBookmakerClient(
		bookmaker.WithMargin(0.05),
		bookmaker.WithMaxStake(100),
		bookmaker.WithOfferTTL(30*time.Second),
	)

	svc := &paperTradeService{
		logger:   logger,
		provider: provider,
		store:    store,
		betStore: betStore,
		book:     book,
		sport:    sport,
		season:   season,
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

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

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
	logger   *slog.Logger
	provider marketdata.OddsProvider
	store    marketdata.LineStore
	betStore bettracking.BetStore
	book     *bookmaker.SimulatedBookmakerClient
	sport    marketdata.Sport
	season   string
}

func (s *paperTradeService) poll(ctx context.Context) {
	events, err := s.provider.Events(ctx, s.sport, s.season)
	if err != nil {
		s.logger.Error("fetching events", "error", err)
		return
	}
	for _, ev := range events {
		markets, err := s.provider.Markets(ctx, ev.ID)
		if err != nil {
			s.logger.Error("fetching markets", "event_id", ev.ID, "error", err)
			continue
		}
		for _, mkt := range markets {
			lines, err := s.provider.Lines(ctx, mkt.ID)
			if err != nil {
				s.logger.Error("fetching lines", "market_id", mkt.ID, "error", err)
				continue
			}
			if err := s.store.SaveLines(ctx, lines); err != nil {
				s.logger.Error("saving lines", "market_id", mkt.ID, "error", err)
			}
			s.evaluateMarket(ctx, mkt, lines)
		}
	}
}

func (s *paperTradeService) evaluateMarket(ctx context.Context, mkt marketdata.Market, lines []marketdata.Line) {
	for _, line := range lines {
		s.book.SetMarket(mkt.ID, string(line.Side), line.ImpliedProb)
	}

	offers, err := s.book.GetOffers(ctx, mkt.ID)
	if err != nil {
		s.logger.Error("getting offers", "market_id", mkt.ID, "error", err)
		return
	}
	for _, offer := range offers {
		// Simple edge check: only bet if offered odds imply >5% edge over the true prob.
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
			EventID:     mkt.EventID,
			MarketID:    mkt.ID,
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
