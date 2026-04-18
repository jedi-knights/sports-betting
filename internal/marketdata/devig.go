package marketdata

import "time"

// Devig applies proportional margin removal to a set of raw implied probabilities.
// The inputs are expected to sum to greater than 1.0 (the overround / vig).
// Each output probability is rescaled so the outputs sum to exactly 1.0.
// Returns nil for a nil or empty input.
func Devig(rawProbs []float64) []float64 {
	if len(rawProbs) == 0 {
		return nil
	}
	var sum float64
	for _, p := range rawProbs {
		sum += p
	}
	result := make([]float64, len(rawProbs))
	for i, p := range rawProbs {
		result[i] = p / sum
	}
	return result
}

// snapshotKey groups lines from the same book for the same market at the same moment.
// Lines sharing a key represent all sides of one market offer and must be devigged together.
type snapshotKey struct {
	marketID   string
	bookID     string
	recordedAt time.Time
}

// DevigLines sets ImpliedProb on each line by grouping lines into market snapshots
// (same market, same book, same recorded_at) and applying proportional devig within each group.
// Lines with no peers in their snapshot receive ImpliedProb = RawImpliedProb.
func DevigLines(lines []Line) []Line {
	groups := make(map[snapshotKey][]int)
	for i, l := range lines {
		k := snapshotKey{l.MarketID, l.BookID, l.RecordedAt}
		groups[k] = append(groups[k], i)
	}

	result := make([]Line, len(lines))
	copy(result, lines)

	for _, indices := range groups {
		rawProbs := make([]float64, len(indices))
		for j, idx := range indices {
			rawProbs[j] = result[idx].RawImpliedProb
		}
		devigged := Devig(rawProbs)
		for j, idx := range indices {
			result[idx].ImpliedProb = devigged[j]
		}
	}
	return result
}
