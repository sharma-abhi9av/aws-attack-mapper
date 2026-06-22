package database

import (
	"context"
	"fmt"
	"log"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
)

var Driver neo4j.DriverWithContext

func Init(uri, user, password string) error {
	var err error
	Driver, err = neo4j.NewDriverWithContext(uri, neo4j.BasicAuth(user, password, ""))
	if err != nil {
		return fmt.Errorf("neo4j driver: %w", err)
	}
	if err = Driver.VerifyConnectivity(context.Background()); err != nil {
		return fmt.Errorf("neo4j connect: %w", err)
	}
	log.Printf("[neo4j] connected to %s", uri)
	return nil
}

func Close() {
	if Driver != nil {
		Driver.Close(context.Background())
	}
}

func RunQuery(ctx context.Context, cypher string, params map[string]any) ([]*neo4j.Record, error) {
	session := Driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeRead})
	defer session.Close(ctx)

	result, err := session.Run(ctx, cypher, params)
	if err != nil {
		return nil, err
	}
	return result.Collect(ctx)
}

func RunWrite(ctx context.Context, cypher string, params map[string]any) ([]*neo4j.Record, error) {
	session := Driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
	defer session.Close(ctx)
	result, err := session.Run(ctx, cypher, params)
	if err != nil {
		return nil, err
	}
	return result.Collect(ctx)
}

func WriteTx(ctx context.Context, fn func(tx neo4j.ManagedTransaction) (any, error)) (any, error) {
	session := Driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
	defer session.Close(ctx)
	return session.ExecuteWrite(ctx, fn)
}
