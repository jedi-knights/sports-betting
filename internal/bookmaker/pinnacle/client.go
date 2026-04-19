package pinnacle

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/jedi-knights/sports-betting/internal/bookmaker"
)

// Client implements bookmaker.BookmakerClient against Pinnacle's REST API.
// Safe for concurrent use.
type Client struct {
	cfg Config
}

// NewClient returns a Client configured with cfg.
func NewClient(cfg Config) *Client {
	return &Client{cfg: cfg}
}

// GetOffers fetches current moneyline prices for a Pinnacle event ID.
// marketID must be the numeric Pinnacle event ID (e.g., "12345").
func (c *Client) GetOffers(ctx context.Context, marketID string) ([]bookmaker.LineOffer, error) {
	url := fmt.Sprintf("%s/v1/fixtures/special/markets?eventId=%s", c.cfg.baseURL(), marketID)
	var fr fixturesResponse
	if err := c.get(ctx, url, &fr); err != nil {
		return nil, fmt.Errorf("pinnacle GetOffers: %w", err)
	}

	now := time.Now()
	var offers []bookmaker.LineOffer
	for _, league := range fr.Leagues {
		for _, ev := range league.Events {
			evID := fmt.Sprintf("%d", ev.ID)
			if evID != marketID {
				continue
			}
			for _, line := range ev.Lines {
				side, _ := line["side"].(string)
				price, _ := line["price"].(float64)
				maxBet, _ := line["maxBet"].(float64)
				if side == "" || price <= 0 {
					continue
				}
				offers = append(offers, bookmaker.LineOffer{
					OfferID:     fmt.Sprintf("%s:%s:%s", c.cfg.baseURL(), evID, side),
					MarketID:    marketID,
					Side:        side,
					DecimalOdds: price,
					MaxStake:    maxBet,
					ExpiresAt:   now.Add(30 * time.Second),
				})
			}
		}
	}
	return offers, nil
}

// PlaceBet submits a straight bet to Pinnacle.
// The OfferID is expected to contain the Pinnacle event ID; see GetOffers.
func (c *Client) PlaceBet(ctx context.Context, req bookmaker.BetRequest) (bookmaker.BetResponse, error) {
	body := map[string]any{
		"uniqueRequestId": req.OfferID,
		"acceptBetterLine": false,
		"stake":            req.RequestedStake,
		"currency":         "USD",
		"oddsFormat":       "Decimal",
		"betType":          "MONEYLINE",
		"eventId":          req.MarketID,
		"period":           0,
		"team":             pinnacleTeam(req.Side),
	}

	var resp placeBetResponse
	if err := c.post(ctx, c.cfg.baseURL()+"/v2/bets/straight", body, &resp); err != nil {
		return bookmaker.BetResponse{}, fmt.Errorf("pinnacle PlaceBet: %w", err)
	}

	switch resp.Status {
	case "ACCEPTED", "PENDING_ACCEPTANCE":
		return bookmaker.BetResponse{
			BetID:         resp.BetID.String(),
			AcceptedStake: req.RequestedStake,
			DecimalOdds:   req.DecimalOdds,
			Filled:        true,
		}, nil
	default:
		return bookmaker.BetResponse{
			Rejected:        true,
			RejectionReason: fmt.Sprintf("status=%s errorCode=%s", resp.Status, resp.ErrorCode),
		}, nil
	}
}

// get performs an authenticated GET request and decodes the JSON response into dst.
func (c *Client) get(ctx context.Context, url string, dst any) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	req.SetBasicAuth(c.cfg.Username, c.cfg.Password)
	return c.do(req, dst)
}

// post performs an authenticated POST request with a JSON body and decodes the response into dst.
func (c *Client) post(ctx context.Context, url string, body any, dst any) error {
	b, err := json.Marshal(body)
	if err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, strings.NewReader(string(b)))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.SetBasicAuth(c.cfg.Username, c.cfg.Password)
	return c.do(req, dst)
}

func (c *Client) do(req *http.Request, dst any) error {
	resp, err := c.cfg.httpClient().Do(req)
	if err != nil {
		return err
	}
	defer func() { _ = resp.Body.Close() }()

	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, body)
	}
	return json.NewDecoder(resp.Body).Decode(dst)
}

// pinnacleTeam maps our side string to Pinnacle's team parameter.
func pinnacleTeam(side string) string {
	switch side {
	case "home":
		return "Team1"
	case "away":
		return "Team2"
	default:
		return side
	}
}
