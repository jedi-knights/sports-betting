package bettracking

// PerformanceReport summarises P&L and quality metrics across a set of settled bets.
type PerformanceReport struct {
	TotalBets   int     `json:"total_bets"`
	WonBets     int     `json:"won_bets"`
	LostBets    int     `json:"lost_bets"`
	TotalStaked float64 `json:"total_staked"`
	TotalProfit float64 `json:"total_profit"`
	ROI         float64 `json:"roi"`
	WinRate     float64 `json:"win_rate"`
}

// ComputePerformanceReport aggregates a slice of BetResult into a PerformanceReport.
// Returns a zero report for an empty slice.
func ComputePerformanceReport(results []BetResult) PerformanceReport {
	if len(results) == 0 {
		return PerformanceReport{}
	}

	var staked, profit float64
	var won, lost int

	for _, r := range results {
		staked += r.Bet.Stake
		profit += r.PnL
		if r.Won {
			won++
		} else {
			lost++
		}
	}

	roi := 0.0
	if staked > 0 {
		roi = profit / staked
	}

	return PerformanceReport{
		TotalBets:   len(results),
		WonBets:     won,
		LostBets:    lost,
		TotalStaked: staked,
		TotalProfit: profit,
		ROI:         roi,
		WinRate:     float64(won) / float64(len(results)),
	}
}
