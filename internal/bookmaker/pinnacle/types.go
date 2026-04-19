// Package pinnacle implements the BookmakerClient and AccountManager ports
// using Pinnacle's REST API (https://pinnacleapi.github.io/).
//
// All requests use HTTP Basic authentication with the account username and password.
// Credentials must be supplied via Config — never hardcoded.
package pinnacle

import (
	"encoding/json"
	"net/http"
	"time"
)

// Config holds the credentials and base URL for Pinnacle API access.
// BaseURL defaults to the production endpoint when empty.
type Config struct {
	// BaseURL is the Pinnacle API root. Override for testing.
	// Default: https://api.pinnacle.com
	BaseURL  string
	Username string
	Password string
	// HTTPClient allows injecting a custom http.Client (e.g., with timeouts).
	// Defaults to a client with a 10-second timeout when nil.
	HTTPClient *http.Client
}

func (c Config) baseURL() string {
	if c.BaseURL != "" {
		return c.BaseURL
	}
	return "https://api.pinnacle.com"
}

func (c Config) httpClient() *http.Client {
	if c.HTTPClient != nil {
		return c.HTTPClient
	}
	return &http.Client{Timeout: 10 * time.Second}
}

// --- Pinnacle API response types ---

type balanceResponse struct {
	AvailableBalance float64 `json:"availableBalance"`
	Currency         string  `json:"currency"`
}

type maxStakeResponse struct {
	MaxRiskStake float64 `json:"maxRiskStake"`
	MaxWinStake  float64 `json:"maxWinStake"`
}

// placeBetResponse holds the Pinnacle bet placement result.
// BetID uses json.Number rather than float64 to preserve the exact integer value
// returned by the API — large Pinnacle bet IDs exceed float64 precision.
type placeBetResponse struct {
	Status    string      `json:"status"`
	BetID     json.Number `json:"betId"`
	ErrorCode string      `json:"errorCode"`
}

type fixtureEvent struct {
	ID    int              `json:"id"`
	Home  string           `json:"home"`
	Away  string           `json:"away"`
	Lines []map[string]any `json:"lines"`
}

type fixtureLeague struct {
	ID     int            `json:"id"`
	Events []fixtureEvent `json:"events"`
}

type fixturesResponse struct {
	Leagues []fixtureLeague `json:"leagues"`
}
