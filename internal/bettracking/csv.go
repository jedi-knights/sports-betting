package bettracking

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
	"sync"
	"time"
)

var csvHeader = []string{
	"id", "event_id", "market_id", "side",
	"stake", "decimal_odds", "model_prob", "edge",
	"placed_at", "status", "clv",
}

// CSVBetStore persists bets to a CSV file.
// Intended for backtesting output; not optimised for concurrent write-heavy workloads.
type CSVBetStore struct {
	path string
	mu   sync.Mutex
}

// NewCSVBetStore creates a CSVBetStore backed by the given file path.
// If the file does not exist it is created with a header row.
func NewCSVBetStore(path string) (*CSVBetStore, error) {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		f, err := os.Create(path)
		if err != nil {
			return nil, err
		}
		w := csv.NewWriter(f)
		if writeErr := w.Write(csvHeader); writeErr != nil {
			_ = f.Close()
			return nil, writeErr
		}
		w.Flush()
		if err := f.Close(); err != nil {
			return nil, err
		}
	}
	return &CSVBetStore{path: path}, nil
}

// Save appends a new bet row. Returns ErrDuplicateID if the ID already exists.
func (s *CSVBetStore) Save(bet Bet) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	all, err := s.readAll()
	if err != nil {
		return err
	}
	for _, b := range all {
		if b.ID == bet.ID {
			return fmt.Errorf("%w: %s", ErrDuplicateID, bet.ID)
		}
	}

	f, err := os.OpenFile(s.path, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	w := csv.NewWriter(f)
	if err := w.Write(betToRow(bet)); err != nil {
		_ = f.Close()
		return err
	}
	w.Flush()
	if flushErr := w.Error(); flushErr != nil {
		_ = f.Close()
		return flushErr
	}
	return f.Close()
}

// FindByID returns the bet with the given ID. Returns ErrNotFound if absent.
func (s *CSVBetStore) FindByID(id string) (Bet, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	all, err := s.readAll()
	if err != nil {
		return Bet{}, err
	}
	for _, b := range all {
		if b.ID == id {
			return b, nil
		}
	}
	return Bet{}, fmt.Errorf("%w: %s", ErrNotFound, id)
}

// FindAll returns all stored bets in file order.
func (s *CSVBetStore) FindAll() ([]Bet, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.readAll()
}

// FindByStatus returns all bets matching the given status.
func (s *CSVBetStore) FindByStatus(status BetStatus) ([]Bet, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	all, err := s.readAll()
	if err != nil {
		return nil, err
	}
	var out []Bet
	for _, b := range all {
		if b.Status == status {
			out = append(out, b)
		}
	}
	return out, nil
}

// Update replaces an existing bet in the file. Returns ErrNotFound if absent.
func (s *CSVBetStore) Update(bet Bet) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	all, err := s.readAll()
	if err != nil {
		return err
	}
	found := false
	for i, b := range all {
		if b.ID == bet.ID {
			all[i] = bet
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("%w: %s", ErrNotFound, bet.ID)
	}
	return s.writeAll(all)
}

// FindByEventID returns all bets associated with the given event ID.
func (s *CSVBetStore) FindByEventID(eventID string) ([]Bet, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	all, err := s.readAll()
	if err != nil {
		return nil, err
	}
	var out []Bet
	for _, b := range all {
		if b.EventID == eventID {
			out = append(out, b)
		}
	}
	return out, nil
}

// Resolve marks a bet won or lost and rewrites the file.
func (s *CSVBetStore) Resolve(betID string, won bool) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	all, err := s.readAll()
	if err != nil {
		return err
	}
	found := false
	for i, b := range all {
		if b.ID == betID {
			if won {
				all[i].Status = BetStatusWon
			} else {
				all[i].Status = BetStatusLost
			}
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("%w: %s", ErrNotFound, betID)
	}
	return s.writeAll(all)
}

// ResolveCLV computes and stores the closing line value, then rewrites the file.
func (s *CSVBetStore) ResolveCLV(betID string, closingDecimalOdds float64) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	all, err := s.readAll()
	if err != nil {
		return err
	}
	found := false
	for i, b := range all {
		if b.ID == betID {
			clv := 1.0/closingDecimalOdds - 1.0/b.DecimalOdds
			all[i].CLV = &clv
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("%w: %s", ErrNotFound, betID)
	}
	return s.writeAll(all)
}

func (s *CSVBetStore) readAll() ([]Bet, error) {
	f, err := os.Open(s.path)
	if err != nil {
		return nil, err
	}
	defer func() { _ = f.Close() }()

	records, err := csv.NewReader(f).ReadAll()
	if err != nil {
		return nil, err
	}
	if len(records) <= 1 {
		return nil, nil
	}

	bets := make([]Bet, 0, len(records)-1)
	for _, row := range records[1:] {
		b, err := rowToBet(row)
		if err != nil {
			return nil, err
		}
		bets = append(bets, b)
	}
	return bets, nil
}

func (s *CSVBetStore) writeAll(bets []Bet) error {
	f, err := os.Create(s.path)
	if err != nil {
		return err
	}
	w := csv.NewWriter(f)
	if err := w.Write(csvHeader); err != nil {
		_ = f.Close()
		return err
	}
	for _, b := range bets {
		if err := w.Write(betToRow(b)); err != nil {
			_ = f.Close()
			return err
		}
	}
	w.Flush()
	if flushErr := w.Error(); flushErr != nil {
		_ = f.Close()
		return flushErr
	}
	return f.Close()
}

func betToRow(b Bet) []string {
	clv := ""
	if b.CLV != nil {
		clv = strconv.FormatFloat(*b.CLV, 'f', 10, 64)
	}
	return []string{
		b.ID,
		b.EventID,
		b.MarketID,
		b.Side,
		strconv.FormatFloat(b.Stake, 'f', 10, 64),
		strconv.FormatFloat(b.DecimalOdds, 'f', 10, 64),
		strconv.FormatFloat(b.ModelProb, 'f', 10, 64),
		strconv.FormatFloat(b.Edge, 'f', 10, 64),
		b.PlacedAt.UTC().Format(time.RFC3339),
		string(b.Status),
		clv,
	}
}

func rowToBet(row []string) (Bet, error) {
	if len(row) != 11 {
		return Bet{}, fmt.Errorf("expected 11 fields, got %d", len(row))
	}
	stake, err := strconv.ParseFloat(row[4], 64)
	if err != nil {
		return Bet{}, fmt.Errorf("parsing stake: %w", err)
	}
	decimalOdds, err := strconv.ParseFloat(row[5], 64)
	if err != nil {
		return Bet{}, fmt.Errorf("parsing decimal_odds: %w", err)
	}
	modelProb, err := strconv.ParseFloat(row[6], 64)
	if err != nil {
		return Bet{}, fmt.Errorf("parsing model_prob: %w", err)
	}
	edge, err := strconv.ParseFloat(row[7], 64)
	if err != nil {
		return Bet{}, fmt.Errorf("parsing edge: %w", err)
	}
	placedAt, err := time.Parse(time.RFC3339, row[8])
	if err != nil {
		return Bet{}, fmt.Errorf("parsing placed_at: %w", err)
	}
	var clvPtr *float64
	if row[10] != "" {
		clv, err := strconv.ParseFloat(row[10], 64)
		if err != nil {
			return Bet{}, fmt.Errorf("parsing clv: %w", err)
		}
		clvPtr = &clv
	}
	return Bet{
		ID:          row[0],
		EventID:     row[1],
		MarketID:    row[2],
		Side:        row[3],
		Stake:       stake,
		DecimalOdds: decimalOdds,
		ModelProb:   modelProb,
		Edge:        edge,
		PlacedAt:    placedAt,
		Status:      BetStatus(row[9]),
		CLV:         clvPtr,
	}, nil
}
