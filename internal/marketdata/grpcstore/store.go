// Package grpcstore provides a LineStore implementation that reads market data
// from a remote market-data service over gRPC.  It is intentionally read-only:
// SaveLines returns an error because writes belong exclusively to market-data.
package grpcstore

import (
	"context"
	"errors"
	"time"

	"google.golang.org/grpc"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	pb "github.com/jedi-knights/sports-betting/internal/marketdata/pb"
)

var _ marketdata.LineStore = (*GRPCLineStore)(nil)

// GRPCLineStore satisfies marketdata.LineStore by calling the market-data gRPC service.
// It is safe for concurrent use — the underlying gRPC ClientConn is thread-safe.
type GRPCLineStore struct {
	client pb.MarketDataServiceClient
}

// New returns a GRPCLineStore using the provided gRPC connection.
// The caller owns the connection lifetime; Close is not called here.
func New(conn grpc.ClientConnInterface) *GRPCLineStore {
	return &GRPCLineStore{client: pb.NewMarketDataServiceClient(conn)}
}

// SaveLines always returns an error — this adapter is read-only.
// Writes are the exclusive responsibility of the market-data service.
func (s *GRPCLineStore) SaveLines(_ context.Context, _ []marketdata.Line) error {
	return errors.New("grpcstore: SaveLines is not supported on the read-only gRPC adapter")
}

// Lines returns all stored lines for the given market.
func (s *GRPCLineStore) Lines(ctx context.Context, marketID string) ([]marketdata.Line, error) {
	resp, err := s.client.ListLines(ctx, &pb.ListLinesRequest{MarketId: marketID})
	if err != nil {
		return nil, err
	}
	return fromProtoLines(resp.Lines), nil
}

// ClosingLine returns the most recent closing line for the given market and side,
// or nil if none exists.
func (s *GRPCLineStore) ClosingLine(ctx context.Context, marketID string, side marketdata.Side) (*marketdata.Line, error) {
	resp, err := s.client.GetClosingLine(ctx, &pb.GetClosingLineRequest{
		MarketId: marketID,
		Side:     string(side),
	})
	if err != nil {
		return nil, err
	}
	if resp.Line == nil {
		return nil, nil
	}
	l := fromProtoLine(resp.Line)
	return &l, nil
}

// Markets returns the distinct set of market IDs that have at least one saved line.
func (s *GRPCLineStore) Markets(ctx context.Context) ([]string, error) {
	resp, err := s.client.ListMarkets(ctx, &pb.ListMarketsRequest{})
	if err != nil {
		return nil, err
	}
	return resp.MarketIds, nil
}

func fromProtoLines(lines []*pb.Line) []marketdata.Line {
	out := make([]marketdata.Line, len(lines))
	for i, l := range lines {
		out[i] = fromProtoLine(l)
	}
	return out
}

func fromProtoLine(l *pb.Line) marketdata.Line {
	var recAt time.Time
	if l.RecordedAt != nil {
		recAt = l.RecordedAt.AsTime()
	}
	return marketdata.Line{
		ID:             l.Id,
		EventID:        l.EventId,
		MarketID:       l.MarketId,
		BookID:         l.BookId,
		Side:           marketdata.Side(l.Side),
		Label:          l.Label,
		AmericanOdds:   int(l.AmericanOdds),
		DecimalOdds:    l.DecimalOdds,
		RawImpliedProb: l.RawImpliedProb,
		ImpliedProb:    l.ImpliedProb,
		Spread:         l.Spread,
		Total:          l.Total,
		RecordedAt:     recAt,
		IsClosing:      l.IsClosing,
	}
}
