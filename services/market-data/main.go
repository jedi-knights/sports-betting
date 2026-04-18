// Command market-data polls an OddsProvider on a schedule, persists lines into a
// LineStore, and exposes the data to other services via a REST API and a gRPC API.
package main

import (
	"context"
	"fmt"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/grpc"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/grpcserver"
	"github.com/jedi-knights/sports-betting/internal/marketdata/httpapi"
	pb "github.com/jedi-knights/sports-betting/internal/marketdata/pb"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	sport := marketdata.Sport(envOr("SPORT", "nfl"))
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
		"sport", sport,
		"season", season,
		"poll_interval", pollInterval,
	)

	ticker := time.NewTicker(pollInterval)
	defer ticker.Stop()

	poll(ctx, logger, provider, store, sport, season)
	for {
		select {
		case <-ticker.C:
			poll(ctx, logger, provider, store, sport, season)
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
	if dsn := os.Getenv("DATABASE_URL"); dsn != "" {
		store, err := marketdata.NewPostgresLineStore(ctx, dsn)
		if err != nil {
			return nil, fmt.Errorf("connecting to postgres: %w", err)
		}
		logger.Info("using postgres line store")
		return store, nil
	}
	logger.Warn("DATABASE_URL not set — using in-memory line store (data will not persist)")
	return marketdata.NewMemoryLineStore(), nil
}

func poll(
	ctx context.Context,
	logger *slog.Logger,
	provider marketdata.OddsProvider,
	store marketdata.LineStore,
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
			// Denormalize event ID onto each line so consumers of the LineStore
			// can cross-reference bets back to events without a separate lookup.
			for i := range lines {
				lines[i].EventID = ev.ID
			}
			if err := store.SaveLines(ctx, lines); err != nil {
				logger.Error("saving lines", "market_id", mkt.ID, "error", err)
			}
		}
	}
	logger.Info("poll complete", "events", len(events))
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
