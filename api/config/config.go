package config

import "os"

type Config struct {
	Neo4jURI      string
	Neo4jUser     string
	Neo4jPassword string
	ListenAddr    string
	OutputDir     string
}

func Load() *Config {
	return &Config{
		Neo4jURI:      getEnv("NEO4J_URI", "bolt://localhost:7687"),
		Neo4jUser:     getEnv("NEO4J_USER", "neo4j"),
		Neo4jPassword: getEnv("NEO4J_PASSWORD", "mooaws123"),
		ListenAddr:    getEnv("LISTEN_ADDR", ":8080"),
		OutputDir:     getEnv("OUTPUT_DIR", "../output"),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
