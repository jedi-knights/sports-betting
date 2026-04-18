package grpcserver_test

import (
	"context"
	"net"
	"testing"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/test/bufconn"

	"github.com/jedi-knights/sports-betting/internal/marketdata"
	"github.com/jedi-knights/sports-betting/internal/marketdata/grpcserver"
	pb "github.com/jedi-knights/sports-betting/internal/marketdata/pb"
)

const bufSize = 1024 * 1024

func startServer(t *testing.T, store marketdata.LineStore) pb.MarketDataServiceClient {
	t.Helper()
	lis := bufconn.Listen(bufSize)
	srv := grpc.NewServer()
	pb.RegisterMarketDataServiceServer(srv, grpcserver.New(store))
	t.Cleanup(func() { srv.Stop() })
	go func() { _ = srv.Serve(lis) }()

	conn, err := grpc.NewClient(
		"passthrough:///bufnet",
		grpc.WithContextDialer(func(ctx context.Context, _ string) (net.Conn, error) {
			return lis.DialContext(ctx)
		}),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		t.Fatalf("connecting to bufconn: %v", err)
	}
	t.Cleanup(func() { _ = conn.Close() })
	return pb.NewMarketDataServiceClient(conn)
}

func TestListMarkets(t *testing.T) {
	store := marketdata.NewMemoryLineStore()
	ctx := context.Background()

	ts := time.Now()
	if err := store.SaveLines(ctx, []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts},
		{ID: "l2", MarketID: "m2", BookID: "b1", Side: marketdata.SideAway, RecordedAt: ts},
	}); err != nil {
		t.Fatalf("seed: %v", err)
	}

	client := startServer(t, store)

	resp, err := client.ListMarkets(ctx, &pb.ListMarketsRequest{})
	if err != nil {
		t.Fatalf("ListMarkets: %v", err)
	}
	if len(resp.MarketIds) != 2 {
		t.Fatalf("got %d market IDs, want 2", len(resp.MarketIds))
	}
}

func TestListLines(t *testing.T) {
	store := marketdata.NewMemoryLineStore()
	ctx := context.Background()

	ts := time.Now()
	want := []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts},
		{ID: "l2", MarketID: "m1", BookID: "b2", Side: marketdata.SideAway, RecordedAt: ts},
	}
	if err := store.SaveLines(ctx, want); err != nil {
		t.Fatalf("seed: %v", err)
	}

	client := startServer(t, store)

	resp, err := client.ListLines(ctx, &pb.ListLinesRequest{MarketId: "m1"})
	if err != nil {
		t.Fatalf("ListLines: %v", err)
	}
	if len(resp.Lines) != 2 {
		t.Fatalf("got %d lines, want 2", len(resp.Lines))
	}
}

func TestListLines_Empty(t *testing.T) {
	client := startServer(t, marketdata.NewMemoryLineStore())
	resp, err := client.ListLines(context.Background(), &pb.ListLinesRequest{MarketId: "unknown"})
	if err != nil {
		t.Fatalf("ListLines: %v", err)
	}
	if len(resp.Lines) != 0 {
		t.Fatalf("got %d lines, want 0", len(resp.Lines))
	}
}

func TestGetClosingLine(t *testing.T) {
	store := marketdata.NewMemoryLineStore()
	ctx := context.Background()

	ts := time.Now()
	closing := marketdata.Line{ID: "cl1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts, IsClosing: true}
	if err := store.SaveLines(ctx, []marketdata.Line{closing}); err != nil {
		t.Fatalf("seed: %v", err)
	}

	client := startServer(t, store)

	resp, err := client.GetClosingLine(ctx, &pb.GetClosingLineRequest{MarketId: "m1", Side: "home"})
	if err != nil {
		t.Fatalf("GetClosingLine: %v", err)
	}
	if resp.Line == nil {
		t.Fatal("expected a closing line, got nil")
	}
	if resp.Line.Id != "cl1" {
		t.Fatalf("got line ID %q, want %q", resp.Line.Id, "cl1")
	}
}

func TestGetClosingLine_NotFound(t *testing.T) {
	client := startServer(t, marketdata.NewMemoryLineStore())
	resp, err := client.GetClosingLine(context.Background(), &pb.GetClosingLineRequest{MarketId: "none", Side: "home"})
	if err != nil {
		t.Fatalf("GetClosingLine: %v", err)
	}
	if resp.Line != nil {
		t.Fatalf("expected nil line, got %+v", resp.Line)
	}
}
