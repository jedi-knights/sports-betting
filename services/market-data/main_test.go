package main

import (
	"testing"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

func TestParseSports(t *testing.T) {
	tests := []struct {
		input string
		want  []marketdata.Sport
	}{
		{"nba", []marketdata.Sport{marketdata.SportNBA}},
		{"nba,nfl", []marketdata.Sport{marketdata.SportNBA, marketdata.SportNFL}},
		{"nba,nfl,mlb,nhl", []marketdata.Sport{marketdata.SportNBA, marketdata.SportNFL, marketdata.SportMLB, marketdata.SportNHL}},
		{"  nba , nfl  ", []marketdata.Sport{marketdata.SportNBA, marketdata.SportNFL}},
		{"", []marketdata.Sport{marketdata.SportNFL}},
	}
	for _, tc := range tests {
		got := parseSports(tc.input)
		if len(got) != len(tc.want) {
			t.Errorf("parseSports(%q): got %v, want %v", tc.input, got, tc.want)
			continue
		}
		for i := range tc.want {
			if got[i] != tc.want[i] {
				t.Errorf("parseSports(%q)[%d]: got %q, want %q", tc.input, i, got[i], tc.want[i])
			}
		}
	}
}
