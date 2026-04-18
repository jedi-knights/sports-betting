package pinnacle

import (
	"context"
	"fmt"
)

// AccountManager implements bookmaker.AccountManager against Pinnacle's REST API.
// Safe for concurrent use.
type AccountManager struct {
	client *Client
}

// NewAccountManager returns an AccountManager that queries Pinnacle for balance and limits.
func NewAccountManager(cfg Config) *AccountManager {
	return &AccountManager{client: NewClient(cfg)}
}

// Balance returns the current available balance from Pinnacle's /v1/client/balance endpoint.
func (a *AccountManager) Balance(ctx context.Context) (float64, error) {
	var resp balanceResponse
	if err := a.client.get(ctx, a.client.cfg.baseURL()+"/v1/client/balance", &resp); err != nil {
		return 0, fmt.Errorf("pinnacle Balance: %w", err)
	}
	return resp.AvailableBalance, nil
}

// MaxStake queries Pinnacle's bet validation endpoint for the maximum risk stake.
// marketID and side are used to construct the query parameters when the bookmaker
// exposes per-event limits; Pinnacle returns a single account-level cap here.
func (a *AccountManager) MaxStake(ctx context.Context, _, _ string) (float64, error) {
	var resp maxStakeResponse
	url := a.client.cfg.baseURL() + "/v1/bets/straight/bet"
	if err := a.client.get(ctx, url, &resp); err != nil {
		return 0, fmt.Errorf("pinnacle MaxStake: %w", err)
	}
	return resp.MaxRiskStake, nil
}
