package marketdata_test

import (
	"math"
	"testing"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
)

func TestAmericanToDecimal(t *testing.T) {
	tests := []struct {
		name     string
		american marketdata.AmericanOdds
		want     float64
		wantErr  bool
	}{
		{"positive underdog", +150, 2.50, false},
		{"negative favorite", -110, 1.9090909, false},
		{"even money positive", +100, 2.00, false},
		{"even money negative", -100, 2.00, false},
		{"large favorite", -300, 1.3333333, false},
		{"large underdog", +300, 4.00, false},
		{"zero is invalid", 0, 0, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := tt.american.ToDecimal()
			if (err != nil) != tt.wantErr {
				t.Fatalf("ToDecimal() error = %v, wantErr %v", err, tt.wantErr)
			}
			if !tt.wantErr && math.Abs(float64(got)-tt.want) > 1e-4 {
				t.Errorf("ToDecimal() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestDecimalToImpliedProbability(t *testing.T) {
	tests := []struct {
		name    string
		decimal marketdata.DecimalOdds
		want    float64
		wantErr bool
	}{
		{"2.0 is 0.50", 2.0, 0.50, false},
		{"2.5 is 0.40", 2.5, 0.40, false},
		{"1.5 is 0.6667", 1.5, 2.0 / 3.0, false},
		{"exactly 1.0 is invalid", 1.0, 0, true},
		{"below 1.0 is invalid", 0.5, 0, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := tt.decimal.ToImpliedProbability()
			if (err != nil) != tt.wantErr {
				t.Fatalf("ToImpliedProbability() error = %v, wantErr %v", err, tt.wantErr)
			}
			if !tt.wantErr && math.Abs(float64(got)-tt.want) > 1e-9 {
				t.Errorf("ToImpliedProbability() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestFractionalToDecimal(t *testing.T) {
	tests := []struct {
		name    string
		frac    marketdata.FractionalOdds
		want    float64
		wantErr bool
	}{
		{"3/2 is 2.5", marketdata.FractionalOdds{Numerator: 3, Denominator: 2}, 2.5, false},
		{"10/11 is ~1.909", marketdata.FractionalOdds{Numerator: 10, Denominator: 11}, 1.9090909, false},
		{"1/1 (evens) is 2.0", marketdata.FractionalOdds{Numerator: 1, Denominator: 1}, 2.0, false},
		{"zero denominator is invalid", marketdata.FractionalOdds{Numerator: 1, Denominator: 0}, 0, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := tt.frac.ToDecimal()
			if (err != nil) != tt.wantErr {
				t.Fatalf("ToDecimal() error = %v, wantErr %v", err, tt.wantErr)
			}
			if !tt.wantErr && math.Abs(float64(got)-tt.want) > 1e-4 {
				t.Errorf("ToDecimal() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestImpliedProbabilityToDecimal(t *testing.T) {
	tests := []struct {
		name    string
		prob    marketdata.ImpliedProbability
		want    float64
		wantErr bool
	}{
		{"0.5 is 2.0", 0.5, 2.0, false},
		{"0.4 is 2.5", 0.4, 2.5, false},
		{"0.0 is invalid", 0.0, 0, true},
		{"1.0 is invalid", 1.0, 0, true},
		{"above 1.0 is invalid", 1.5, 0, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := tt.prob.ToDecimal()
			if (err != nil) != tt.wantErr {
				t.Fatalf("ToDecimal() error = %v, wantErr %v", err, tt.wantErr)
			}
			if !tt.wantErr && math.Abs(float64(got)-tt.want) > 1e-9 {
				t.Errorf("ToDecimal() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestAmericanDecimalRoundtrip(t *testing.T) {
	cases := []marketdata.AmericanOdds{-110, +150, -200, +300, +100, -100}
	for _, american := range cases {
		decimal, err := american.ToDecimal()
		if err != nil {
			t.Fatalf("american %d: ToDecimal: %v", american, err)
		}
		prob, err := decimal.ToImpliedProbability()
		if err != nil {
			t.Fatalf("american %d: ToImpliedProbability: %v", american, err)
		}
		back, err := prob.ToDecimal()
		if err != nil {
			t.Fatalf("american %d: prob.ToDecimal: %v", american, err)
		}
		if math.Abs(float64(decimal)-float64(back)) > 1e-9 {
			t.Errorf("american %d: roundtrip decimal %v → prob → %v", american, decimal, back)
		}
	}
}
