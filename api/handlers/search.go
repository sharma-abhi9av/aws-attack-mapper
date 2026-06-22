package handlers

import (
	"context"

	"github.com/anomalyco/mooaws/api/database"
	"github.com/anomalyco/mooaws/api/models"
	"github.com/gofiber/fiber/v2"
)

func Search(c *fiber.Ctx) error {
	q := c.Query("q", "")
	if q == "" {
		return c.JSON([]models.SearchResult{})
	}

	ctx := context.Background()
	rows, err := database.RunQuery(ctx, database.CypherSearch, map[string]any{"q": q})
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}

	results := make([]models.SearchResult, 0, len(rows))
	for _, row := range rows {
		m := row.AsMap()
		results = append(results, models.SearchResult{
			ID:       strVal(m["id"]),
			Name:     strVal(m["name"]),
			Type:     strVal(m["label"]),
			Subtitle: strVal(m["arn"]),
		})
	}
	return c.JSON(results)
}
