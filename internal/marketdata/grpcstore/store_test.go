// Package grpcstore_test verifies GRPCLineStore by spinning up a real in-process
// gRPC server backed by a MemoryLineStore and confirming the adapter translates
// protobuf responses back into the marketdata domain types correctly.
package grpcstore_test

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
	"github.com/jedi-knights/sports-betting/internal/marketdata/grpcstore"
	pb "github.com/jedi-knights/sports-betting/internal/marketdata/pb"
)

const bufSize = 1024 * 1024

func seedAndConnect(t *testing.T, lines []marketdata.Line) marketdata.LineStore {
	t.Helper()
	backing := marketdata.NewMemoryLineStore()
	if len(lines) > 0 {
		if err := backing.SaveLines(context.Background(), lines); err != nil {
			t.Fatalf("seed: %v", err)
		}
	}

	lis := bufconn.Listen(bufSize)
	srv := grpc.NewServer()
	pb.RegisterMarketDataServiceServer(srv, grpcserver.New(backing))
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
	return grpcstore.New(conn)
}

func TestGRPCLineStore_Markets(t *testing.T) {
	ts := time.Now()
	store := seedAndConnect(t, []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome, RecordedAt: ts},
		{ID: "l2", MarketID: "m2", BookID: "b1", Side: marketdata.SideAway, RecordedAt: ts},
	})

	ids, err := store.Markets(context.Background())
	if err != nil {
		t.Fatalf("Markets: %v", err)
	}
	if len(ids) != 2 {
		t.Fatalf("got %d market IDs, want 2", len(ids))
	}
}

func TestGRPCLineStore_Lines(t *testing.T) {
	ts := time.Now()
	store := seedAndConnect(t, []marketdata.Line{
		{ID: "l1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome,
			DecimalOdds: 2.1, RecordedAt: ts},
		{ID: "l2", MarketID: "m1", BookID: "b2", Side: marketdata.SideAway,
			DecimalOdds: 1.9, RecordedAt: ts},
	})

	lines, err := store.Lines(context.Background(), "m1")
	if err != nil {
		t.Fatalf("Lines: %v", err)
	}
	if len(lines) != 2 {
		t.Fatalf("got %d lines, want 2", len(lines))
	}
	if lines[0].DecimalOdds == 0 {
		t.Fatal("decimal odds not deserialized")
	}
}

func TestGRPCLineStore_Lines_Empty(t *testing.T) {
	store := seedAndConnect(t, nil)
	lines, err := store.Lines(context.Background(), "unknown")
	if err != nil {
		t.Fatalf("Lines: %v", err)
	}
	if len(lines) != 0 {
		t.Fatalf("got %d lines, want 0", len(lines))
	}
}

func TestGRPCLineStore_ClosingLine(t *testing.T) {
	ts := time.Now()
	store := seedAndConnect(t, []marketdata.Line{
		{ID: "cl1", MarketID: "m1", BookID: "b1", Side: marketdata.SideHome,
			RecordedAt: ts, IsClosing: true},
	})

	line, err := store.ClosingLine(context.Background(), "m1", marketdata.SideHome)
	if err != nil {
		t.Fatalf("ClosingLine: %v", err)
	}
	if line == nil {
		t.Fatal("expected closing line, got nil")
	}
	if line.ID != "cl1" {
		t.Fatalf("got ID %q, want cl1", line.ID)
	}
}

func TestGRPCLineStore_ClosingLine_NotFound(t *testing.T) {
	store := seedAndConnect(t, nil)
	line, err := store.ClosingLine(context.Background(), "none", marketdata.SideHome)
	if err != nil {
		t.Fatalf("ClosingLine: %v", err)
	}
	if line != nil {
		t.Fatalf("expected nil, got %+v", line)
	}
}

// SaveLines is owned by market-data; this adapter is read-only.
// Calling it must return a clear error rather than panic.
func TestGRPCLineStore_SaveLines_Unsupported(t *testing.T) {
	store := seedAndConnect(t, nil)
	err := store.SaveLines(context.Background(), nil)
	if err == nil {
		t.Fatal("expected error for SaveLines on read-only adapter, got nil")
	}
}
