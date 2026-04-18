// Command market-data polls an OddsProvider on a schedule, persists lines into
// a CachingLineStore (Valkey → Postgres), publishes LinesUpdated events to
// Kafka after each market snapshot, and exposes the data via REST and gRPC APIs.
package main

import (
	"context"
	"fmt"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"google.golang.org/grpc"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/cachestore"
	"github.com/jedi-knights/sports-betting/internal/marketdata/grpcserver"
	"github.com/jedi-knights/sports-betting/internal/marketdata/httpapi"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkapub"
	pb "github.com/jedi-knights/sports-betting/internal/marketdata/pb"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	sports := parseSports(os.Getenv("SPORT"))
	season := envOr("SEASON", "2024")
	pollInterval := durationEnv("POLL_INTERVAL_SECONDS", 60)
	httpAddr := envOr("ADDR", ":8081")
	grpcAddr := envOr("GRPC_ADDR", ":9090")

	var provider marketdata.OddsProvider
	if apiKey := os.Getenv("ODDS_API_KEY"); apiKey != "" {
		provider = marketdata.NewTheOddsAPIProvider(apiKey)
		logger.Info("using live odds provider", "source", "the-odds-api.com")
	} else {
		dataPath := envOr("DATA_PATH", "/data/odds.json")
		p, err := marketdata.NewStaticOddsProvider(dataPath)
		if err != nil {
			logger.Warn("static odds file unavailable, starting with null provider", "path", dataPath, "error", err)
			provider = marketdata.NullOddsProvider{}
		} else {
			provider = p
			logger.Info("using static odds provider", "path", dataPath)
		}
	}

	store, err := buildLineStore(ctx, logger)
	if err != nil {
		logger.Error("building line store", "error", err)
		os.Exit(1)
	}
	if closer, ok := store.(interface{ Close() }); ok {
		defer closer.Close()
	}

	publisher := buildPublisher(logger)
	defer func() { _ = publisher.Close() }()

	// Start gRPC server.
	grpcSrv := grpc.NewServer()
	pb.RegisterMarketDataServiceServer(grpcSrv, grpcserver.New(store))
	grpcLis, err := net.Listen("tcp", grpcAddr)
	if err != nil {
		logger.Error("listening for gRPC", "addr", grpcAddr, "error", err)
		os.Exit(1)
	}
	go func() {
		logger.Info("market-data gRPC server listening", "addr", grpcAddr)
		if err := grpcSrv.Serve(grpcLis); err != nil {
			logger.Error("gRPC server error", "error", err)
		}
	}()

	// Start HTTP server.
	httpSrv := &http.Server{
		Addr:         httpAddr,
		Handler:      httpapi.New(store),
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}
	go func() {
		logger.Info("market-data HTTP server listening", "addr", httpAddr)
		if err := httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("HTTP server error", "error", err)
		}
	}()

	logger.Info("market-data service starting",
		"sports", sports,
		"season", season,
		"poll_interval", pollInterval,
	)

	ticker := time.NewTicker(pollInterval)
	defer ticker.Stop()

	pollAll(ctx, logger, provider, store, publisher, sports, season)
	for {
		select {
		case <-ticker.C:
			pollAll(ctx, logger, provider, store, publisher, sports, season)
		case <-ctx.Done():
			logger.Info("market-data service shutting down")
			grpcSrv.GracefulStop()
			shutCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			_ = httpSrv.Shutdown(shutCtx)
			return
		}
	}
}

func buildLineStore(ctx context.Context, logger *slog.Logger) (marketdata.LineStore, error) {
	if dsn := os.Getenv("DATABASE_URL"); dsn == "" {
		logger.Warn("DATABASE_URL not set — using in-memory line store (data will not persist)")
		return marketdata.NewMemoryLineStore(), nil
	}
	pg, err := marketdata.NewPostgresLineStore(ctx, os.Getenv("DATABASE_URL"))
	if err != nil {
		return nil, fmt.Errorf("connecting to postgres: %w", err)
	}
	if valkeyAddr := os.Getenv("VALKEY_ADDR"); valkeyAddr != "" {
		vc, err := cachestore.NewValkeyCache(valkeyAddr)
		if err != nil {
			logger.Warn("valkey unavailable, running without cache", "addr", valkeyAddr, "error", err)
			return pg, nil
		}
		logger.Info("using postgres line store with valkey cache", "valkey", valkeyAddr)
		return cachestore.New(pg, vc, time.Minute), nil
	}
	logger.Info("using postgres line store (no cache)")
	return pg, nil
}

func buildPublisher(logger *slog.Logger) marketdata.EventPublisher {
	brokerList := os.Getenv("KAFKA_BROKERS")
	topic := envOr("KAFKA_TOPIC", "market-data.lines")
	if brokerList == "" {
		logger.Warn("KAFKA_BROKERS not set — events will not be published")
		return marketdata.NullEventPublisher{}
	}
	brokers := strings.Split(brokerList, ",")
	pub, err := kafkapub.New(brokers, topic)
	if err != nil {
		logger.Warn("kafka publisher unavailable, falling back to null publisher", "error", err)
		return marketdata.NullEventPublisher{}
	}
	logger.Info("publishing events to kafka", "brokers", brokers, "topic", topic)
	return pub
}

func pollAll(
	ctx context.Context,
	logger *slog.Logger,
	provider marketdata.OddsProvider,
	store marketdata.LineStore,
	publisher marketdata.EventPublisher,
	sports []marketdata.Sport,
	season string,
) {
	for _, sport := range sports {
		poll(ctx, logger, provider, store, publisher, sport, season)
	}
}

func poll(
	ctx context.Context,
	logger *slog.Logger,
	provider marketdata.OddsProvider,
	store marketdata.LineStore,
	publisher marketdata.EventPublisher,
	sport marketdata.Sport,
	season string,
) {
	events, err := provider.Events(ctx, sport, season)
	if err != nil {
		logger.Error("fetching events", "error", err)
		return
	}
	for _, ev := range events {
		markets, err := provider.Markets(ctx, ev.ID)
		if err != nil {
			logger.Error("fetching markets", "event_id", ev.ID, "error", err)
			continue
		}
		for _, mkt := range markets {
			lines, err := provider.Lines(ctx, mkt.ID)
			if err != nil {
				logger.Error("fetching lines", "market_id", mkt.ID, "error", err)
				continue
			}
			for i := range lines {
				lines[i].EventID = ev.ID
			}
			if err := store.SaveLines(ctx, lines); err != nil {
				logger.Error("saving lines", "market_id", mkt.ID, "error", err)
				continue
			}
			event := marketdata.LinesUpdatedEvent{
				MarketID:   mkt.ID,
				EventID:    ev.ID,
				Lines:      lines,
				RecordedAt: time.Now(),
			}
			if err := publisher.PublishLinesUpdated(ctx, event); err != nil {
				logger.Error("publishing event", "market_id", mkt.ID, "error", err)
			}
		}
	}
	logger.Info("poll complete", "sport", sport, "events", len(events))
}

func parseSports(raw string) []marketdata.Sport {
	if raw == "" {
		return []marketdata.Sport{marketdata.SportNFL}
	}
	parts := strings.Split(raw, ",")
	sports := make([]marketdata.Sport, 0, len(parts))
	for _, p := range parts {
		if s := strings.TrimSpace(p); s != "" {
			sports = append(sports, marketdata.Sport(s))
		}
	}
	if len(sports) == 0 {
		return []marketdata.Sport{marketdata.SportNFL}
	}
	return sports
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
