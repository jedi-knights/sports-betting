// Package kafkasub consumes market-data domain events from a Kafka topic.
package kafkasub

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"

	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

// EventHandler is the handler type for LinesUpdatedEvent messages.
// Returning a non-nil error is logged by the subscriber but does not stop the loop.
type EventHandler = func(ctx context.Context, event marketdata.LinesUpdatedEvent) error

// KafkaSubscriber consumes LinesUpdatedEvents from a Kafka topic.
type KafkaSubscriber = Subscriber[marketdata.LinesUpdatedEvent]

// New returns a KafkaSubscriber joined to the given consumer group.
func New(brokers []string, groupID, topic string, logger *slog.Logger) (*KafkaSubscriber, error) {
	return newSubscriber[marketdata.LinesUpdatedEvent](brokers, groupID, topic, logger)
}

// Subscriber is a type-parameterised Kafka consumer. It polls a single topic
// and dispatches each record to a caller-supplied handler after JSON decoding.
// Safe for concurrent use.
type Subscriber[E any] struct {
	client *kgo.Client
	logger *slog.Logger
}

// newSubscriber is the shared generic constructor used by New and NewScoresSubscriber.
func newSubscriber[E any](brokers []string, groupID, topic string, logger *slog.Logger) (*Subscriber[E], error) {
	client, err := kgo.NewClient(
		kgo.SeedBrokers(brokers...),
		kgo.ConsumerGroup(groupID),
		kgo.ConsumeTopics(topic),
	)
	if err != nil {
		return nil, fmt.Errorf("creating kafka consumer: %w", err)
	}
	return &Subscriber[E]{client: client, logger: logger}, nil
}

// Subscribe polls the broker in a blocking loop and calls handler for each decoded event.
// Unmarshal failures and handler errors are logged at Error level but do not stop the loop.
// Returns nil when ctx is cancelled; returns a wrapped error on broker failures.
func (s *Subscriber[E]) Subscribe(ctx context.Context, handler func(context.Context, E) error) error {
	for {
		fetches := s.client.PollFetches(ctx)
		if err := fetches.Err(); err != nil {
			if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
				return nil
			}
			return fmt.Errorf("polling kafka: %w", err)
		}
		fetches.EachRecord(func(r *kgo.Record) {
			var event E
			if err := json.Unmarshal(r.Value, &event); err != nil {
				s.logger.Error("failed to unmarshal kafka record",
					"topic", r.Topic,
					"partition", r.Partition,
					"offset", r.Offset,
					"error", err)
				return
			}
			if err := handler(ctx, event); err != nil {
				s.logger.Error("event handler error",
					"topic", r.Topic,
					"partition", r.Partition,
					"offset", r.Offset,
					"error", err)
			}
		})
		s.client.AllowRebalance()
	}
}

// Close closes the underlying Kafka client.
// kgo.Client.Close is synchronous and does not return an error.
func (s *Subscriber[E]) Close() error {
	s.client.Close()
	return nil
}
