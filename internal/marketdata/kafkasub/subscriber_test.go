package kafkasub_test

import (
	"context"
	"io"
	"log/slog"
	"sync/atomic"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkapub"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkasub"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkatest"
)

func discardLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

// TestScoresSubscriber_ReceivesPublishedEvent verifies round-trip publish/consume
// of GameCompletedEvent through a real Kafka broker.
func TestScoresSubscriber_ReceivesPublishedEvent(t *testing.T) {
	addrs := kafkatest.Brokers(t)
	topic := "test.scores." + t.Name()
	group := "test-scores-group-" + t.Name()

	pub, err := kafkapub.New(addrs, topic+".lines", topic)
	if err != nil {
		t.Fatalf("publisher: %v", err)
	}
	defer func() { _ = pub.Close() }()

	sub, err := kafkasub.NewScoresSubscriber(addrs, group, topic, discardLogger())
	if err != nil {
		t.Fatalf("scores subscriber: %v", err)
	}
	defer func() {
		if err := sub.Close(); err != nil {
			t.Errorf("closing scores subscriber: %v", err)
		}
	}()

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	event := marketdata.GameCompletedEvent{
		Result: marketdata.GameResult{
			EventID:   "ev1",
			HomeTeam:  "Chiefs",
			AwayTeam:  "Ravens",
			HomeScore: 27,
			AwayScore: 20,
		},
		RecordedAt: time.Now(),
	}
	if err := pub.PublishGameCompleted(ctx, event); err != nil {
		t.Fatalf("publish: %v", err)
	}

	var received atomic.Int32
	go func() {
		_ = sub.Subscribe(ctx, func(_ context.Context, e marketdata.GameCompletedEvent) error {
			if e.Result.EventID == event.Result.EventID {
				received.Add(1)
				cancel()
			}
			return nil
		})
	}()

	<-ctx.Done()
	if received.Load() == 0 {
		t.Fatal("no GameCompletedEvent received within timeout")
	}
}

func TestKafkaSubscriber_ReceivesPublishedEvent(t *testing.T) {
	addrs := kafkatest.Brokers(t)
	topic := "test.sub." + t.Name()
	group := "test-group-" + t.Name()

	pub, err := kafkapub.New(addrs, topic, topic+".scores")
	if err != nil {
		t.Fatalf("publisher: %v", err)
	}
	defer func() { _ = pub.Close() }()

	sub, err := kafkasub.New(addrs, group, topic, discardLogger())
	if err != nil {
		t.Fatalf("subscriber: %v", err)
	}
	defer func() {
		if err := sub.Close(); err != nil {
			t.Errorf("closing subscriber: %v", err)
		}
	}()

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	event := marketdata.LinesUpdatedEvent{
		MarketID:   "m1",
		EventID:    "ev1",
		RecordedAt: time.Now(),
		Lines:      []marketdata.Line{{ID: "l1", MarketID: "m1", Side: marketdata.SideHome}},
	}
	if err := pub.PublishLinesUpdated(ctx, event); err != nil {
		t.Fatalf("publish: %v", err)
	}

	var received atomic.Int32
	go func() {
		_ = sub.Subscribe(ctx, func(_ context.Context, e marketdata.LinesUpdatedEvent) error {
			if e.MarketID == event.MarketID {
				received.Add(1)
				cancel()
			}
			return nil
		})
	}()

	<-ctx.Done()
	if received.Load() == 0 {
		t.Fatal("no event received within timeout")
	}
}
