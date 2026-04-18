// Package kafkapub publishes market-data domain events to a Kafka topic.
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
// events to a Kafka topic, keyed by market ID to preserve per-market ordering.
type KafkaPublisher struct {
	client *kgo.Client
	topic  string
}

// New returns a KafkaPublisher that writes to the given topic.
func New(brokers []string, topic string) (*KafkaPublisher, error) {
	client, err := kgo.NewClient(kgo.SeedBrokers(brokers...))
	if err != nil {
		return nil, fmt.Errorf("creating kafka client: %w", err)
	}
	return &KafkaPublisher{client: client, topic: topic}, nil
}

// PublishLinesUpdated serialises event as JSON and produces it synchronously.
func (p *KafkaPublisher) PublishLinesUpdated(ctx context.Context, event marketdata.LinesUpdatedEvent) error {
	payload, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("marshaling event: %w", err)
	}
	record := &kgo.Record{
		Topic: p.topic,
		Key:   []byte(event.MarketID),
		Value: payload,
	}
	if err := p.client.ProduceSync(ctx, record).FirstErr(); err != nil {
		return fmt.Errorf("producing to kafka: %w", err)
	}
	return nil
}

// Close flushes and closes the underlying Kafka client.
func (p *KafkaPublisher) Close() error {
	p.client.Close()
	return nil
}
