package handlers

import (
	"context"
	"strings"

	"github.com/anomalyco/mooaws/api/database"
	"github.com/anomalyco/mooaws/api/models"
	"github.com/gofiber/fiber/v2"
)

var labelMap = map[string]string{
	"users":           "User",
	"roles":           "Role",
	"groups":          "Group",
	"policies":        "Policy",
	"buckets":         "S3Bucket",
	"instances":       "EC2Instance",
	"security-groups": "SecurityGroup",
}

func listNodes(c *fiber.Ctx, label string) error {
	ctx := context.Background()
	cypher := strings.ReplaceAll(database.CypherAllNodes, "$LABEL", label)
	rows, err := database.RunQuery(ctx, cypher, nil)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}
	type node struct {
		ID   string `json:"id"`
		Name string `json:"name"`
		ARN  string `json:"arn,omitempty"`
	}
	nodes := make([]node, 0, len(rows))
	for _, row := range rows {
		n := node{}
		if v, ok := row.Get("id"); ok && v != nil {
			n.ID = v.(string)
		}
		if v, ok := row.Get("name"); ok && v != nil {
			n.Name = v.(string)
		}
		if v, ok := row.Get("arn"); ok && v != nil {
			n.ARN = v.(string)
		}
		nodes = append(nodes, n)
	}
	return c.JSON(nodes)
}

func getNode(c *fiber.Ctx, label string) error {
	id := c.Params("id")
	ctx := context.Background()

	row, err := database.RunQuery(ctx, database.CypherNodeByID, map[string]any{"id": id})
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}
	if len(row) == 0 {
		return c.Status(404).JSON(fiber.Map{"error": "not found"})
	}

	labels, _ := row[0].Get("labels")
	props, _ := row[0].Get("props")

	result := models.Node{
		ID:     id,
		Labels: toStringSlice(labels),
		Props:  toMap(props),
	}
	return c.JSON(result)
}

func ListNodes(c *fiber.Ctx) error {
	label, ok := labelMap[c.Params("type")]
	if !ok {
		return c.Status(400).JSON(fiber.Map{"error": "unknown type"})
	}
	return listNodes(c, label)
}

func GetNode(c *fiber.Ctx) error {
	label, ok := labelMap[c.Params("type")]
	if !ok {
		return c.Status(400).JSON(fiber.Map{"error": "unknown type"})
	}
	return getNode(c, label)
}

func toMap(v any) map[string]any {
	if m, ok := v.(map[string]any); ok {
		return m
	}
	return nil
}

func toStringSlice(v any) []string {
	if l, ok := v.([]any); ok {
		s := make([]string, 0, len(l))
		for _, item := range l {
			if str, ok := item.(string); ok {
				s = append(s, str)
			}
		}
		return s
	}
	return nil
}
