// Package kafkasub consumes market-data domain events from a Kafka topic.
package kafkasub

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

// EventHandler is called for each LinesUpdatedEvent received from the broker.
// Returning a non-nil error logs the failure but does not stop the subscriber.
type EventHandler func(ctx context.Context, event marketdata.LinesUpdatedEvent) error

// KafkaSubscriber consumes LinesUpdatedEvents from a Kafka topic and dispatches
// them to a registered handler.  It commits offsets after each successful poll.
type KafkaSubscriber struct {
	client *kgo.Client
}

// New returns a KafkaSubscriber joined to the given consumer group.
func New(brokers []string, groupID, topic string) (*KafkaSubscriber, error) {
	client, err := kgo.NewClient(
		kgo.SeedBrokers(brokers...),
		kgo.ConsumerGroup(groupID),
		kgo.ConsumeTopics(topic),
	)
	if err != nil {
		return nil, fmt.Errorf("creating kafka consumer: %w", err)
	}
	return &KafkaSubscriber{client: client}, nil
}

// Subscribe polls the broker in a blocking loop and calls handler for each
// received event.  It returns when ctx is cancelled.
func (s *KafkaSubscriber) Subscribe(ctx context.Context, handler EventHandler) error {
	for {
		fetches := s.client.PollFetches(ctx)
		if err := fetches.Err(); err != nil {
			if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
				return nil
			}
			return fmt.Errorf("polling kafka: %w", err)
		}
		fetches.EachRecord(func(r *kgo.Record) {
			var event marketdata.LinesUpdatedEvent
			if err := json.Unmarshal(r.Value, &event); err != nil {
				return
			}
			_ = handler(ctx, event)
		})
		s.client.AllowRebalance()
	}
}

// Close closes the underlying Kafka client.
func (s *KafkaSubscriber) Close() error {
	s.client.Close()
	return nil
}
