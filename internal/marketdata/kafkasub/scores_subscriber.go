package kafkasub

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

// GameCompletedHandler is called for each GameCompletedEvent received from the broker.
// Returning a non-nil error logs the failure but does not stop the subscriber.
type GameCompletedHandler func(ctx context.Context, event marketdata.GameCompletedEvent) error

// ScoresSubscriber consumes GameCompletedEvents from a Kafka topic and dispatches
// them to a registered handler.  It commits offsets after each successful poll.
type ScoresSubscriber struct {
	client *kgo.Client
}

// NewScoresSubscriber returns a ScoresSubscriber joined to the given consumer group.
func NewScoresSubscriber(brokers []string, groupID, topic string) (*ScoresSubscriber, error) {
	client, err := kgo.NewClient(
		kgo.SeedBrokers(brokers...),
		kgo.ConsumerGroup(groupID),
		kgo.ConsumeTopics(topic),
	)
	if err != nil {
		return nil, fmt.Errorf("creating kafka scores consumer: %w", err)
	}
	return &ScoresSubscriber{client: client}, nil
}

// Subscribe polls the broker in a blocking loop and calls handler for each
// received GameCompletedEvent.  It returns when ctx is cancelled.
func (s *ScoresSubscriber) Subscribe(ctx context.Context, handler GameCompletedHandler) error {
	for {
		fetches := s.client.PollFetches(ctx)
		if err := fetches.Err(); err != nil {
			if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
				return nil
			}
			return fmt.Errorf("polling kafka scores: %w", err)
		}
		fetches.EachRecord(func(r *kgo.Record) {
			var event marketdata.GameCompletedEvent
			if err := json.Unmarshal(r.Value, &event); err != nil {
				return
			}
			_ = handler(ctx, event)
		})
		s.client.AllowRebalance()
	}
}

// Close closes the underlying Kafka client.
func (s *ScoresSubscriber) Close() error {
	s.client.Close()
	return nil
}
