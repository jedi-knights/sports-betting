// Command paper-trade subscribes to LinesUpdated events from the market-data
// Kafka topic, evaluates each market snapshot through a SimulatedBookmakerClient,
// records paper bets, and exposes a REST API for monitoring performance.
package main

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/jedi-knights/sports-betting/internal/bettracking"
	"github.com/jedi-knights/sports-betting/internal/bookmaker"
	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkasub"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	addr := envOr("ADDR", ":8080")
	kafkaBrokers := strings.Split(envOr("KAFKA_BROKERS", "kafka:9092"), ",")
	kafkaTopic := envOr("KAFKA_TOPIC", "market-data.lines")
	kafkaGroup := envOr("KAFKA_GROUP", "paper-trade")

	sub, err := kafkasub.New(kafkaBrokers, kafkaGroup, kafkaTopic)
	if err != nil {
		logger.Error("creating kafka subscriber", "error", err)
		os.Exit(1)
	}
	defer func() { _ = sub.Close() }()
	logger.Info("subscribed to kafka", "brokers", kafkaBrokers, "topic", kafkaTopic, "group", kafkaGroup)

	betStore := bettracking.NewMemoryBetStore()
	book := bookmaker.NewSimulatedBookmakerClient(
		bookmaker.WithMargin(0.05),
		bookmaker.WithMaxStake(100),
		bookmaker.WithOfferTTL(30*time.Second),
	)

	svc := &paperTradeService{
		logger:   logger,
		betStore: betStore,
		book:     book,
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

	// Block on the Kafka subscription loop; returns when ctx is cancelled.
	if err := sub.Subscribe(ctx, svc.handleLinesUpdated); err != nil {
		if !errors.Is(err, context.Canceled) {
			logger.Error("kafka subscriber error", "error", err)
		}
	}

	logger.Info("paper-trade service shutting down")
	shutCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = server.Shutdown(shutCtx)
}

type paperTradeService struct {
	logger   *slog.Logger
	betStore bettracking.BetStore
	book     *bookmaker.SimulatedBookmakerClient
}

// handleLinesUpdated is called by the Kafka subscriber for each LinesUpdated event.
func (s *paperTradeService) handleLinesUpdated(ctx context.Context, event marketdata.LinesUpdatedEvent) error {
	s.evaluateMarket(ctx, event.MarketID, event.EventID, event.Lines)
	return nil
}

func (s *paperTradeService) evaluateMarket(ctx context.Context, marketID, eventID string, lines []marketdata.Line) {
	for _, line := range lines {
		s.book.SetMarket(marketID, string(line.Side), line.ImpliedProb)
	}

	offers, err := s.book.GetOffers(ctx, marketID)
	if err != nil {
		s.logger.Error("getting offers", "market_id", marketID, "error", err)
		return
	}
	for _, offer := range offers {
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

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
