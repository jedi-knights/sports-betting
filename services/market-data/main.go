// Command market-data polls an OddsProvider on a schedule and persists lines
// into a LineStore. It is the data-ingestion service for the paper-trading stack.
package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	sport := marketdata.Sport(envOr("SPORT", "nfl"))
	season := envOr("SEASON", "2024")
	pollInterval := durationEnv("POLL_INTERVAL_SECONDS", 60)

	var provider marketdata.OddsProvider
	if apiKey := os.Getenv("ODDS_API_KEY"); apiKey != "" {
		provider = marketdata.NewTheOddsAPIProvider(apiKey)
		logger.Info("using live odds provider", "source", "the-odds-api.com")
	} else {
		dataPath := envOr("DATA_PATH", "/data/odds.json")
		p, err := marketdata.NewStaticOddsProvider(dataPath)
		if err != nil {
			logger.Error("loading static odds provider", "path", dataPath, "error", err)
			os.Exit(1)
		}
		provider = p
		logger.Info("using static odds provider", "path", dataPath)
	}
	store := marketdata.NewMemoryLineStore()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	logger.Info("market-data service starting",
		"sport", sport,
		"season", season,
		"poll_interval", pollInterval,
	)

	ticker := time.NewTicker(pollInterval)
	defer ticker.Stop()

	// Run once immediately, then on each tick.
	poll(ctx, logger, provider, store, sport, season)
	for {
		select {
		case <-ticker.C:
			poll(ctx, logger, provider, store, sport, season)
		case <-ctx.Done():
			logger.Info("market-data service shutting down")
			return
		}
	}
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
