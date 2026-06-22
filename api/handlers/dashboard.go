package handlers

import (
	"context"

	"github.com/anomalyco/mooaws/api/database"
	"github.com/anomalyco/mooaws/api/models"
	"github.com/gofiber/fiber/v2"
)

func GetStats(c *fiber.Ctx) error {
	ctx := context.Background()

	rows, err := database.RunQuery(ctx, database.CypherStats, nil)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}
	stats := models.Stats{}
	for _, row := range rows {
		label, _ := row.Get("label")
		count, _ := row.Get("count")
		cv := int(count.(int64))
		switch label {
		case "User":
			stats.Users = cv
		case "Role":
			stats.Roles = cv
		case "Group":
			stats.Groups = cv
		case "Policy":
			stats.Policies = cv
		case "S3Bucket":
			stats.Buckets = cv
		case "EC2Instance":
			stats.Instances = cv
		case "SecurityGroup":
			stats.SecurityGroups = cv
		}
	}

	if r, err := database.RunQuery(ctx, database.CypherEdgeCount, nil); err == nil && len(r) > 0 {
		stats.Edges = int(r[0].Values[0].(int64))
	}

	if r, err := database.RunQuery(ctx, database.CypherEdgeTypes, nil); err == nil {
		stats.EdgeTypes = make(map[string]int, len(r))
		for _, row := range r {
			if typ, ok := row.Get("type"); ok {
				cnt := int(row.Values[1].(int64))
				stats.EdgeTypes[typ.(string)] = cnt
			}
		}
	}

	high := models.HighValueSummary{}
	if r, err := database.RunQuery(ctx, database.CypherAdminUsers, nil); err == nil && len(r) > 0 {
		high.AdminUsers = int(r[0].Values[0].(int64))
	}
	if r, err := database.RunQuery(ctx, database.CypherOpenSGs, nil); err == nil && len(r) > 0 {
		high.OpenSGs = int(r[0].Values[0].(int64))
	}
	if r, err := database.RunQuery(ctx, database.CypherPublicBuckets, nil); err == nil && len(r) > 0 {
		high.PublicBuckets = int(r[0].Values[0].(int64))
	}
	if r, err := database.RunQuery(ctx, database.CypherLeakyRoles, nil); err == nil && len(r) > 0 {
		high.LeakyRoles = int(r[0].Values[0].(int64))
	}
	stats.HighValueTargets = high

	return c.JSON(stats)
}
