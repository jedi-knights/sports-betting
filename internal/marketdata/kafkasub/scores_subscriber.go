package kafkasub

import (
	"context"
	"log/slog"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

// GameCompletedHandler is the handler type for GameCompletedEvent messages.
// Returning a non-nil error is logged by the subscriber but does not stop the loop.
type GameCompletedHandler = func(ctx context.Context, event marketdata.GameCompletedEvent) error

// ScoresSubscriber consumes GameCompletedEvents from a Kafka topic.
type ScoresSubscriber = Subscriber[marketdata.GameCompletedEvent]

// NewScoresSubscriber returns a ScoresSubscriber joined to the given consumer group.
func NewScoresSubscriber(brokers []string, groupID, topic string, logger *slog.Logger) (*ScoresSubscriber, error) {
	return newSubscriber[marketdata.GameCompletedEvent](brokers, groupID, topic, logger)
}
