package marketdata_test

import (
	"testing"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

func TestGameResult_WinningSide(t *testing.T) {
	tests := []struct {
		name      string
		home, away int
		want      marketdata.Side
	}{
		{"home wins", 110, 105, marketdata.SideHome},
		{"away wins", 98, 107, marketdata.SideAway},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			// Arrange
			r := marketdata.GameResult{HomeScore: tc.home, AwayScore: tc.away}

			// Act
			got := r.WinningSide()

			// Assert
			if got != tc.want {
				t.Errorf("WinningSide() = %q, want %q", got, tc.want)
			}
		})
	}
}

func TestGameResult_WinningSide_Draw(t *testing.T) {
	// Arrange
	r := marketdata.GameResult{HomeScore: 100, AwayScore: 100}

	// Act
	got := r.WinningSide()

	// Assert
	if got != marketdata.SideDraw {
		t.Errorf("WinningSide() = %q, want draw", got)
	}
}
