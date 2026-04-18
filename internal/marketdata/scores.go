package marketdata

import (
	"context"
	"time"
)

// GameResult is the final score of a completed game.
type GameResult struct {
	EventID     string
	Sport       Sport
	HomeTeam    string
	AwayTeam    string
	HomeScore   int
	AwayScore   int
	CompletedAt time.Time
}

// WinningSide returns the Side that won the game.
// Returns SideDraw when scores are equal.
func (r GameResult) WinningSide() Side {
	switch {
	case r.HomeScore > r.AwayScore:
		return SideHome
	case r.AwayScore > r.HomeScore:
		return SideAway
	default:
		return SideDraw
	}
}

// ScoresProvider fetches completed game results from an external source.
// It is a separate interface from OddsProvider because not all odds sources
// also provide score data.
type ScoresProvider interface {
	// Scores returns completed game results for the given sport.
	// daysFrom controls how many days back to include (1–3 for most providers).
	Scores(ctx context.Context, sport Sport, daysFrom int) ([]GameResult, error)
}
