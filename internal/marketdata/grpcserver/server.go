// Package grpcserver exposes a MarketDataService gRPC server backed by a LineStore.
package grpcserver

import (
	"context"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	pb "github.com/jedi-knights/sports-betting/internal/marketdata/pb"
)

var _ pb.MarketDataServiceServer = (*Server)(nil)

// Server implements pb.MarketDataServiceServer by delegating to a LineStore.
type Server struct {
	pb.UnimplementedMarketDataServiceServer
	store marketdata.LineStore
}

// New returns a Server that satisfies pb.MarketDataServiceServer.
func New(store marketdata.LineStore) *Server {
	return &Server{store: store}
}

// ListMarkets returns the distinct market IDs that have at least one saved line.
func (s *Server) ListMarkets(ctx context.Context, _ *pb.ListMarketsRequest) (*pb.ListMarketsResponse, error) {
	ids, err := s.store.Markets(ctx)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "listing markets: %v", err)
	}
	return &pb.ListMarketsResponse{MarketIds: ids}, nil
}

// ListLines returns all stored lines for the given market.
func (s *Server) ListLines(ctx context.Context, req *pb.ListLinesRequest) (*pb.ListLinesResponse, error) {
	lines, err := s.store.Lines(ctx, req.GetMarketId())
	if err != nil {
		return nil, status.Errorf(codes.Internal, "listing lines: %v", err)
	}
	return &pb.ListLinesResponse{Lines: toProtoLines(lines)}, nil
}

// GetClosingLine returns the most recent closing line for the given market and side.
func (s *Server) GetClosingLine(ctx context.Context, req *pb.GetClosingLineRequest) (*pb.GetClosingLineResponse, error) {
	line, err := s.store.ClosingLine(ctx, req.GetMarketId(), marketdata.Side(req.GetSide()))
	if err != nil {
		return nil, status.Errorf(codes.Internal, "getting closing line: %v", err)
	}
	resp := &pb.GetClosingLineResponse{}
	if line != nil {
		resp.Line = toProtoLine(*line)
	}
	return resp, nil
}

func toProtoLines(lines []marketdata.Line) []*pb.Line {
	out := make([]*pb.Line, len(lines))
	for i, l := range lines {
		out[i] = toProtoLine(l)
	}
	return out
}

func toProtoLine(l marketdata.Line) *pb.Line {
	p := &pb.Line{
		Id:             l.ID,
		EventId:        l.EventID,
		MarketId:       l.MarketID,
		BookId:         l.BookID,
		Side:           string(l.Side),
		Label:          l.Label,
		AmericanOdds:   int32(l.AmericanOdds),
		DecimalOdds:    l.DecimalOdds,
		RawImpliedProb: l.RawImpliedProb,
		ImpliedProb:    l.ImpliedProb,
		RecordedAt:     timestamppb.New(l.RecordedAt),
		IsClosing:      l.IsClosing,
	}
	p.Spread = l.Spread
	p.Total = l.Total
	return p
}
