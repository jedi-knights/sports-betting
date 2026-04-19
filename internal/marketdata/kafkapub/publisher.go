// Package kafkapub publishes market-data domain events to Kafka topics.
package kafkapub

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

var _ marketdata.EventPublisher = (*KafkaPublisher)(nil)

// KafkaPublisher implements marketdata.EventPublisher by writing JSON-encoded
// events to Kafka, keyed by a natural identifier for per-entity ordering.
type KafkaPublisher struct {
	client      *kgo.Client
	linesTopic  string
	scoresTopic string
}

// New returns a KafkaPublisher that writes lines events to linesTopic and
// game-completed events to scoresTopic.
func New(brokers []string, linesTopic, scoresTopic string) (*KafkaPublisher, error) {
	client, err := kgo.NewClient(kgo.SeedBrokers(brokers...))
	if err != nil {
		return nil, fmt.Errorf("creating kafka client: %w", err)
	}
	return &KafkaPublisher{client: client, linesTopic: linesTopic, scoresTopic: scoresTopic}, nil
}

// PublishLinesUpdated serialises the event as JSON and produces it synchronously,
// keyed by market ID to preserve per-market ordering.
func (p *KafkaPublisher) PublishLinesUpdated(ctx context.Context, event marketdata.LinesUpdatedEvent) error {
	return p.produce(ctx, p.linesTopic, []byte(event.MarketID), event)
}

// PublishGameCompleted serialises the event as JSON and produces it synchronously,
// keyed by event ID.
func (p *KafkaPublisher) PublishGameCompleted(ctx context.Context, event marketdata.GameCompletedEvent) error {
	return p.produce(ctx, p.scoresTopic, []byte(event.Result.EventID), event)
}

// Close flushes pending records and closes the underlying Kafka client.
// Blocks until all in-flight produce requests complete (franz-go guarantees this).
func (p *KafkaPublisher) Close() error {
	p.client.Close()
	return nil
}

func (p *KafkaPublisher) produce(ctx context.Context, topic string, key []byte, v any) error {
	payload, err := json.Marshal(v)
	if err != nil {
		return fmt.Errorf("marshaling event: %w", err)
	}
	if err := p.client.ProduceSync(ctx, &kgo.Record{
		Topic: topic,
		Key:   key,
		Value: payload,
	}).FirstErr(); err != nil {
		return fmt.Errorf("producing to kafka topic %q: %w", topic, err)
	}
	return nil
}
