package main

import (
	"context"
	"embed"
	"io/fs"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/filesystem"
	"github.com/gofiber/fiber/v2/middleware/logger"

	"github.com/anomalyco/mooaws/api/config"
	"github.com/anomalyco/mooaws/api/database"
	"github.com/anomalyco/mooaws/api/handlers"
	"github.com/anomalyco/mooaws/api/ingest"
)

//go:embed frontend/*
var frontendFS embed.FS

func main() {
	cfg := config.Load()

	if err := database.Init(cfg.Neo4jURI, cfg.Neo4jUser, cfg.Neo4jPassword); err != nil {
		log.Fatalf("neo4j: %v", err)
	}
	defer database.Close()

	app := fiber.New(fiber.Config{AppName: "MooAWS"})

	app.Use(cors.New())
	app.Use(logger.New())

	sub, _ := fs.Sub(frontendFS, "frontend")

	api := app.Group("/api")

	api.Get("/stats", handlers.GetStats)

	api.Get("/ingest", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{"message": "Send POST to ingest"})
	})
	api.Post("/ingest", func(c *fiber.Ctx) error {
		ing := ingest.New(cfg.OutputDir)
		if err := ing.Run(context.Background()); err != nil {
			return c.Status(500).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(fiber.Map{"status": "ok", "message": "Ingestion complete"})
	})
	api.Post("/upload", handlers.UploadAndIngest)

	api.Get("/search", handlers.Search)

	graph := api.Group("/graph")
	graph.Get("/all", handlers.GetAllGraph)
	graph.Get("/neighbors/:id", handlers.GetNeighbors)
	graph.Get("/shortest-path", handlers.GetShortestPath)
	graph.Get("/all-paths", handlers.GetAllPaths)
	graph.Get("/reachable/:id", handlers.GetReachable)
	graph.Get("/high-value", handlers.GetHighValue)
	graph.Put("/owned/:id", handlers.ToggleOwned)

	api.Get("/:type", handlers.ListNodes)
	api.Get("/:type/:id", handlers.GetNode)

	app.Use("/", filesystem.New(filesystem.Config{
		Root:       http.FS(sub),
		PathPrefix: "",
		Index:      "index.html",
	}))

	go func() {
		quit := make(chan os.Signal, 1)
		signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
		<-quit
		log.Println("shutting down...")
		app.Shutdown()
	}()

	log.Printf("MooAWS API listening on %s", cfg.ListenAddr)
	if err := app.Listen(cfg.ListenAddr); err != nil {
		log.Fatalf("listen: %v", err)
	}
}
