package bettracking_test

import (
	"math"
	"testing"

	"github.com/jedi-knights/sports-betting/internal/bettracking"
)

func makeResult(won bool, stake, odds float64) bettracking.BetResult {
	status := bettracking.BetStatusLost
	if won {
		status = bettracking.BetStatusWon
	}
	bet := bettracking.Bet{
		ID:          "b",
		Stake:       stake,
		DecimalOdds: odds,
		Status:      status,
	}
	return bettracking.NewBetResult(bet)
}

func TestComputePerformanceReport_Empty(t *testing.T) {
	// Arrange
	var results []bettracking.BetResult

	// Act
	r := bettracking.ComputePerformanceReport(results)

	// Assert
	if r.TotalBets != 0 {
		t.Errorf("total_bets: want 0, got %d", r.TotalBets)
	}
	if r.ROI != 0 {
		t.Errorf("roi: want 0, got %v", r.ROI)
	}
}

func TestComputePerformanceReport_TotalBets(t *testing.T) {
	results := []bettracking.BetResult{
		makeResult(true, 100, 2.0),
		makeResult(false, 50, 1.9),
	}
	r := bettracking.ComputePerformanceReport(results)
	if r.TotalBets != 2 {
		t.Errorf("total_bets: want 2, got %d", r.TotalBets)
	}
}

func TestComputePerformanceReport_WinRate(t *testing.T) {
	results := []bettracking.BetResult{
		makeResult(true, 100, 2.0),
		makeResult(false, 100, 2.0),
		makeResult(true, 100, 2.0),
		makeResult(false, 100, 2.0),
	}
	r := bettracking.ComputePerformanceReport(results)
	if math.Abs(r.WinRate-0.5) > 1e-9 {
		t.Errorf("win_rate: want 0.5, got %v", r.WinRate)
	}
}

func TestComputePerformanceReport_ROI(t *testing.T) {
	// 1 win at 2.0 odds (stake 100 → profit 100) + 1 loss (stake 100 → profit -100)
	// total_profit = 0, total_staked = 200, ROI = 0
	results := []bettracking.BetResult{
		makeResult(true, 100, 2.0),
		makeResult(false, 100, 2.0),
	}
	r := bettracking.ComputePerformanceReport(results)
	if math.Abs(r.ROI) > 1e-9 {
		t.Errorf("roi: want 0.0, got %v", r.ROI)
	}
}

func TestComputePerformanceReport_PositiveROI(t *testing.T) {
	// 2 wins at 2.0 odds (stake 100 each → profit 100 each) + 1 loss (stake 100)
	// total_profit = 100, total_staked = 300, ROI = 1/3
	results := []bettracking.BetResult{
		makeResult(true, 100, 2.0),
		makeResult(true, 100, 2.0),
		makeResult(false, 100, 2.0),
	}
	r := bettracking.ComputePerformanceReport(results)
	want := 100.0 / 300.0
	if math.Abs(r.ROI-want) > 1e-9 {
		t.Errorf("roi: want %.4f, got %.4f", want, r.ROI)
	}
}

func TestComputePerformanceReport_TotalStaked(t *testing.T) {
	results := []bettracking.BetResult{
		makeResult(true, 75, 2.0),
		makeResult(false, 25, 2.0),
	}
	r := bettracking.ComputePerformanceReport(results)
	if math.Abs(r.TotalStaked-100) > 1e-9 {
		t.Errorf("total_staked: want 100, got %v", r.TotalStaked)
	}
}
