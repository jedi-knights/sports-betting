package kafkasub_test

import (
	"context"
	"os"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkapub"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkasub"
)

func brokers(t *testing.T) []string {
	t.Helper()
	v := os.Getenv("TEST_KAFKA_BROKERS")
	if v == "" {
		t.Skip("TEST_KAFKA_BROKERS not set — skipping Kafka integration test")
	}
	return strings.Split(v, ",")
}

func TestKafkaSubscriber_ReceivesPublishedEvent(t *testing.T) {
	addrs := brokers(t)
	topic := "test.sub." + t.Name()
	group := "test-group-" + t.Name()

	pub, err := kafkapub.New(addrs, topic)
	if err != nil {
		t.Fatalf("publisher: %v", err)
	}
	defer func() { _ = pub.Close() }()

	sub, err := kafkasub.New(addrs, group, topic)
	if err != nil {
		t.Fatalf("subscriber: %v", err)
	}
	defer func() { _ = sub.Close() }()

	event := marketdata.LinesUpdatedEvent{
		MarketID:   "m1",
		EventID:    "ev1",
		RecordedAt: time.Now(),
		Lines:      []marketdata.Line{{ID: "l1", MarketID: "m1", Side: marketdata.SideHome}},
	}
	if err := pub.PublishLinesUpdated(context.Background(), event); err != nil {
		t.Fatalf("publish: %v", err)
	}

	var received atomic.Int32
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

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
