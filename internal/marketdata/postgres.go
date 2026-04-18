package marketdata

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

var _ LineStore = (*PostgresLineStore)(nil)

// PostgresLineStore is a LineStore backed by a PostgreSQL database.
// It uses an upsert on the line ID so repeated polls are idempotent —
// the latest odds for a given line ID always win.
type PostgresLineStore struct {
	pool *pgxpool.Pool
}

// NewPostgresLineStore opens a connection pool and creates the lines table if
// it does not already exist. The caller must call Close when done.
func NewPostgresLineStore(ctx context.Context, connString string) (*PostgresLineStore, error) {
	pool, err := pgxpool.New(ctx, connString)
	if err != nil {
		return nil, fmt.Errorf("opening postgres pool: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("pinging postgres: %w", err)
	}
	s := &PostgresLineStore{pool: pool}
	if err := s.migrate(ctx); err != nil {
		pool.Close()
		return nil, err
	}
	return s, nil
}

// Close releases the connection pool.
func (s *PostgresLineStore) Close() {
	s.pool.Close()
}

// Truncate removes all rows from the lines table.
// It exists solely for use in integration tests.
func (s *PostgresLineStore) Truncate(ctx context.Context) error {
	_, err := s.pool.Exec(ctx, "TRUNCATE TABLE lines")
	return err
}

func (s *PostgresLineStore) migrate(ctx context.Context) error {
	_, err := s.pool.Exec(ctx, `
		CREATE TABLE IF NOT EXISTS lines (
			id               TEXT PRIMARY KEY,
			event_id         TEXT NOT NULL DEFAULT '',
			market_id        TEXT NOT NULL,
			book_id          TEXT NOT NULL,
			side             TEXT NOT NULL,
			label            TEXT NOT NULL DEFAULT '',
			american_odds    INTEGER NOT NULL DEFAULT 0,
			decimal_odds     DOUBLE PRECISION NOT NULL DEFAULT 0,
			raw_implied_prob DOUBLE PRECISION NOT NULL DEFAULT 0,
			implied_prob     DOUBLE PRECISION NOT NULL DEFAULT 0,
			spread           DOUBLE PRECISION,
			total            DOUBLE PRECISION,
			recorded_at      TIMESTAMPTZ NOT NULL,
			is_closing       BOOLEAN NOT NULL DEFAULT FALSE
		);
		CREATE INDEX IF NOT EXISTS lines_market_id_idx ON lines (market_id);
		CREATE INDEX IF NOT EXISTS lines_closing_idx   ON lines (market_id, side) WHERE is_closing = TRUE;
	`)
	if err != nil {
		return fmt.Errorf("running lines migration: %w", err)
	}
	return nil
}

// SaveLines upserts lines into the database keyed by ID.
func (s *PostgresLineStore) SaveLines(ctx context.Context, lines []Line) error {
	batch := &pgx.Batch{}
	const q = `
		INSERT INTO lines (id, event_id, market_id, book_id, side, label,
		                   american_odds, decimal_odds, raw_implied_prob, implied_prob,
		                   spread, total, recorded_at, is_closing)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
		ON CONFLICT (id) DO UPDATE SET
			event_id         = EXCLUDED.event_id,
			american_odds    = EXCLUDED.american_odds,
			decimal_odds     = EXCLUDED.decimal_odds,
			raw_implied_prob = EXCLUDED.raw_implied_prob,
			implied_prob     = EXCLUDED.implied_prob,
			spread           = EXCLUDED.spread,
			total            = EXCLUDED.total,
			recorded_at      = EXCLUDED.recorded_at,
			is_closing       = EXCLUDED.is_closing`
	for _, l := range lines {
		batch.Queue(q,
			l.ID, l.EventID, l.MarketID, l.BookID, string(l.Side), l.Label,
			l.AmericanOdds, l.DecimalOdds, l.RawImpliedProb, l.ImpliedProb,
			l.Spread, l.Total, l.RecordedAt, l.IsClosing,
		)
	}
	results := s.pool.SendBatch(ctx, batch)
	defer func() { _ = results.Close() }()
	for range lines {
		if _, err := results.Exec(); err != nil {
			return fmt.Errorf("executing batch upsert: %w", err)
		}
	}
	return nil
}

// Lines returns all stored lines for the given market, ordered by recorded_at descending.
func (s *PostgresLineStore) Lines(ctx context.Context, marketID string) ([]Line, error) {
	const q = `
		SELECT id, event_id, market_id, book_id, side, label,
		       american_odds, decimal_odds, raw_implied_prob, implied_prob,
		       spread, total, recorded_at, is_closing
		FROM lines
		WHERE market_id = $1
		ORDER BY recorded_at DESC`
	rows, err := s.pool.Query(ctx, q, marketID)
	if err != nil {
		return nil, fmt.Errorf("querying lines: %w", err)
	}
	defer rows.Close()
	return scanLines(rows)
}

// ClosingLine returns the most recent closing line for the given market and side,
// or nil if none exists.
func (s *PostgresLineStore) ClosingLine(ctx context.Context, marketID string, side Side) (*Line, error) {
	const q = `
		SELECT id, event_id, market_id, book_id, side, label,
		       american_odds, decimal_odds, raw_implied_prob, implied_prob,
		       spread, total, recorded_at, is_closing
		FROM lines
		WHERE market_id = $1 AND side = $2 AND is_closing = TRUE
		ORDER BY recorded_at DESC
		LIMIT 1`
	rows, err := s.pool.Query(ctx, q, marketID, string(side))
	if err != nil {
		return nil, fmt.Errorf("querying closing line: %w", err)
	}
	defer rows.Close()
	lines, err := scanLines(rows)
	if err != nil || len(lines) == 0 {
		return nil, err
	}
	return &lines[0], nil
}

// Markets returns the distinct set of market IDs that have at least one saved line.
func (s *PostgresLineStore) Markets(ctx context.Context) ([]string, error) {
	rows, err := s.pool.Query(ctx, "SELECT DISTINCT market_id FROM lines ORDER BY market_id")
	if err != nil {
		return nil, fmt.Errorf("querying markets: %w", err)
	}
	defer rows.Close()
	var ids []string
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			return nil, fmt.Errorf("scanning market id: %w", err)
		}
		ids = append(ids, id)
	}
	return ids, rows.Err()
}

func scanLines(rows pgx.Rows) ([]Line, error) {
	var lines []Line
	for rows.Next() {
		var l Line
		var side string
		if err := rows.Scan(
			&l.ID, &l.EventID, &l.MarketID, &l.BookID, &side, &l.Label,
			&l.AmericanOdds, &l.DecimalOdds, &l.RawImpliedProb, &l.ImpliedProb,
			&l.Spread, &l.Total, &l.RecordedAt, &l.IsClosing,
		); err != nil {
			return nil, fmt.Errorf("scanning line: %w", err)
		}
		l.Side = Side(side)
		lines = append(lines, l)
	}
	return lines, rows.Err()
}
