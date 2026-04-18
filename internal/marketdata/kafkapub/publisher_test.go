package kafkapub_test

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkapub"
	"github.com/jedi-knights/sports-betting/internal/marketdata/kafkatest"
)

func TestKafkaPublisher_PublishLinesUpdated(t *testing.T) {
	addrs := kafkatest.Brokers(t)
	topic := "test.lines." + t.Name()

	pub, err := kafkapub.New(addrs, topic, topic+".scores")
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

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

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

	fetches := consumer.PollFetches(ctx)
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

func TestKafkaPublisher_PublishGameCompleted(t *testing.T) {
	addrs := kafkatest.Brokers(t)
	scoresTopic := "test.scores." + t.Name()

	pub, err := kafkapub.New(addrs, scoresTopic+".lines", scoresTopic)
	if err != nil {
		t.Fatalf("New: %v", err)
	}
	defer func() { _ = pub.Close() }()

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

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := pub.PublishGameCompleted(ctx, event); err != nil {
		t.Fatalf("PublishGameCompleted: %v", err)
	}

	consumer, err := kgo.NewClient(
		kgo.SeedBrokers(addrs...),
		kgo.ConsumeTopics(scoresTopic),
		kgo.ConsumeResetOffset(kgo.NewOffset().AtStart()),
	)
	if err != nil {
		t.Fatalf("creating consumer: %v", err)
	}
	defer consumer.Close()

	fetches := consumer.PollFetches(ctx)
	if err := fetches.Err(); err != nil {
		t.Fatalf("polling: %v", err)
	}
	var got marketdata.GameCompletedEvent
	fetches.EachRecord(func(r *kgo.Record) {
		_ = json.Unmarshal(r.Value, &got)
	})
	if got.Result.EventID != event.Result.EventID {
		t.Fatalf("got event_id %q, want %q", got.Result.EventID, event.Result.EventID)
	}
	if got.Result.HomeScore != 27 {
		t.Fatalf("got HomeScore %d, want 27", got.Result.HomeScore)
	}
}
