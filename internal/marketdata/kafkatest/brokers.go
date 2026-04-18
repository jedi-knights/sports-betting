// Package kafkatest provides shared test helpers for Kafka integration tests.
package kafkatest

import (
	"os"
	"strings"
	"testing"
)

// Brokers returns the Kafka broker addresses from the TEST_KAFKA_BROKERS
// environment variable. If the variable is not set, the test is skipped.
// Used by kafkapub and kafkasub integration tests to avoid duplicating the
// skip-unless-configured pattern.
func Brokers(t *testing.T) []string {
	t.Helper()
	v := os.Getenv("TEST_KAFKA_BROKERS")
	if v == "" {
		t.Skip("TEST_KAFKA_BROKERS not set — skipping Kafka integration test")
	}
	return strings.Split(v, ",")
}
