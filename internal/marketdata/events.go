package marketdata

import (
	"context"
	"time"
)

// LinesUpdatedEvent is published by market-data each time a fresh odds snapshot
// is saved for a market.  It carries the full line slice so consumers do not
// need a follow-up read from the line store.
type LinesUpdatedEvent struct {
	MarketID   string    `json:"market_id"`
	EventID    string    `json:"event_id"`
	Lines      []Line    `json:"lines"`
	RecordedAt time.Time `json:"recorded_at"`
}

// GameCompletedEvent is published by market-data when a game has finished and
// final scores are confirmed.  Consumers use it to settle open bets.
type GameCompletedEvent struct {
	Result     GameResult `json:"result"`
	RecordedAt time.Time  `json:"recorded_at"`
}

// EventPublisher publishes market-data domain events to an event bus.
// Implementations include KafkaPublisher for production and NullEventPublisher
// for development environments without a broker.
type EventPublisher interface {
	PublishLinesUpdated(ctx context.Context, event LinesUpdatedEvent) error
	PublishGameCompleted(ctx context.Context, event GameCompletedEvent) error
	Close() error
}

// NullEventPublisher discards all events.  Used when no broker is configured.
type NullEventPublisher struct{}

func (NullEventPublisher) PublishLinesUpdated(_ context.Context, _ LinesUpdatedEvent) error {
	return nil
}

func (NullEventPublisher) PublishGameCompleted(_ context.Context, _ GameCompletedEvent) error {
	return nil
}

func (NullEventPublisher) Close() error { return nil }
