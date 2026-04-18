package kafkapub_test

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkapub"
)

func brokers(t *testing.T) []string {
	t.Helper()
	v := os.Getenv("TEST_KAFKA_BROKERS")
	if v == "" {
		t.Skip("TEST_KAFKA_BROKERS not set — skipping Kafka integration test")
	}
	return strings.Split(v, ",")
}

func TestKafkaPublisher_PublishLinesUpdated(t *testing.T) {
	addrs := brokers(t)
	topic := "test.lines." + t.Name()

	pub, err := kafkapub.New(addrs, topic)
	if err != nil {
		t.Fatalf("New: %v", err)
	}
	defer func() { _ = pub.Close() }()

	event := marketdata.LinesUpdatedEvent{
		MarketID:   "m1",
		EventID:    "ev1",
		RecordedAt: time.Now(),
		Lines: []marketdata.Line{
			{ID: "l1", MarketID: "m1", Side: marketdata.SideHome, DecimalOdds: 2.1},
		},
	}

	ctx := context.Background()
	if err := pub.PublishLinesUpdated(ctx, event); err != nil {
		t.Fatalf("PublishLinesUpdated: %v", err)
	}

	// Consume the message back and verify round-trip.
	consumer, err := kgo.NewClient(
		kgo.SeedBrokers(addrs...),
		kgo.ConsumeTopics(topic),
		kgo.ConsumeResetOffset(kgo.NewOffset().AtStart()),
	)
	if err != nil {
		t.Fatalf("creating consumer: %v", err)
	}
	defer consumer.Close()

	ctx2, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	fetches := consumer.PollFetches(ctx2)
	if err := fetches.Err(); err != nil {
		t.Fatalf("polling: %v", err)
	}
	var got marketdata.LinesUpdatedEvent
	fetches.EachRecord(func(r *kgo.Record) {
		_ = json.Unmarshal(r.Value, &got)
	})
	if got.MarketID != event.MarketID {
		t.Fatalf("got market_id %q, want %q", got.MarketID, event.MarketID)
	}
	if len(got.Lines) != 1 {
		t.Fatalf("got %d lines, want 1", len(got.Lines))
	}
}
