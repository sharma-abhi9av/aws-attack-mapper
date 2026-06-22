package handlers

import (
	"context"
	"strconv"
	"strings"

	"github.com/anomalyco/mooaws/api/database"
	"github.com/anomalyco/mooaws/api/models"
	"github.com/gofiber/fiber/v2"
	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
)



func GetAllGraph(c *fiber.Ctx) error {
	ctx := context.Background()
	resp := models.GraphResponse{}

	rows, err := database.RunQuery(ctx, database.CypherAllNodesFull, nil)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}
	for _, row := range rows {
		id, _ := row.Get("id")
		labels, _ := row.Get("labels")
		props, _ := row.Get("props")
		resp.Nodes = append(resp.Nodes, models.Node{
			ID:     strVal(id),
			Labels: toStringSlice(labels),
			Props:  toMap(props),
		})
	}

	eRows, err := database.RunQuery(ctx, database.CypherAllEdges, nil)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}
	for _, row := range eRows {
		eid, _ := row.Get("id")
		source, _ := row.Get("source")
		target, _ := row.Get("target")
		relType, _ := row.Get("relType")
		resp.Edges = append(resp.Edges, models.Edge{
			ID:      strVal(eid),
			Source:  strVal(source),
			Target:  strVal(target),
			RelType: strVal(relType),
		})
	}

	return c.JSON(resp)
}

func GetNeighbors(c *fiber.Ctx) error {
	id := c.Params("id")
	ctx := context.Background()

	resp := models.GraphResponse{}

	// Fetch source node
	sourceRows, err := database.RunQuery(ctx, database.CypherNodeByID, map[string]any{"id": id})
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}
	if len(sourceRows) > 0 {
		labels, _ := sourceRows[0].Get("labels")
		props, _ := sourceRows[0].Get("props")
		nodeLabels := toStringSlice(labels)
		nodeProps := toMap(props)
		if nodeLabels == nil {
			nodeLabels = []string{"Node"}
		}
		if nodeProps == nil {
			nodeProps = map[string]any{}
		}
		resp.Nodes = append(resp.Nodes, models.Node{
			ID:     id,
			Labels: nodeLabels,
			Props:  nodeProps,
		})
	}

	// Fetch neighbors
	rows, err := database.RunQuery(ctx, database.CypherNeighbors, map[string]any{"id": id})
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}

	seen := map[string]bool{id: true}

	for _, row := range rows {
		props := row.AsMap()
		nid := strVal(props["id"])
		label := strVal(props["label"])
		name := strVal(props["name"])
		arn := strVal(props["arn"])
		owned, _ := props["owned"].(bool)
		relType := strVal(props["relType"])
		dir := strVal(props["direction"])

		if nid != "" && !seen[nid] {
			seen[nid] = true
			nodeProps := map[string]any{"name": name, "owned": owned}
			if arn != "" {
				nodeProps["arn"] = arn
			}
			resp.Nodes = append(resp.Nodes, models.Node{
				ID:     nid,
				Labels: []string{label},
				Props:  nodeProps,
			})
		}

		edge := models.Edge{
			ID:      strVal(props["relId"]),
			RelType: relType,
		}
		if dir == "out" {
			edge.Source = id
			edge.Target = nid
		} else {
			edge.Source = nid
			edge.Target = id
		}
		resp.Edges = append(resp.Edges, edge)
	}
	return c.JSON(resp)
}

func GetShortestPath(c *fiber.Ctx) error {
	from := c.Query("from")
	to := c.Query("to")
	maxDepth, _ := strconv.Atoi(c.Query("max-depth", "10"))
	if maxDepth < 1 || maxDepth > 20 {
		maxDepth = 10
	}

	ctx := context.Background()
	q := strings.ReplaceAll(database.CypherShortestPath, "$MAXDEPTH", strconv.Itoa(maxDepth))
	rows, err := database.RunQuery(ctx, q, map[string]any{
		"from": from, "to": to,
	})
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}
	if len(rows) == 0 {
		return c.JSON(models.PathResult{})
	}
	return c.JSON(rowToPath(rows[0]))
}

func GetAllPaths(c *fiber.Ctx) error {
	from := c.Query("from")
	to := c.Query("to")
	maxDepth, _ := strconv.Atoi(c.Query("max-depth", "10"))
	if maxDepth < 1 || maxDepth > 20 {
		maxDepth = 10
	}

	ctx := context.Background()
	q := strings.ReplaceAll(database.CypherAllPaths, "$MAXDEPTH", strconv.Itoa(maxDepth))
	rows, err := database.RunQuery(ctx, q, map[string]any{
		"from": from, "to": to,
	})
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}

	paths := make([]models.PathResult, 0, len(rows))
	for _, row := range rows {
		paths = append(paths, rowToPath(row))
	}
	return c.JSON(paths)
}

func GetReachable(c *fiber.Ctx) error {
	id := c.Params("id")
	maxDepth, _ := strconv.Atoi(c.Query("max-depth", "5"))
	if maxDepth < 1 || maxDepth > 10 {
		maxDepth = 5
	}

	ctx := context.Background()
	q := strings.ReplaceAll(database.CypherReachable, "$MAXDEPTH", strconv.Itoa(maxDepth))
	rows, err := database.RunQuery(ctx, q, map[string]any{
		"id": id,
	})
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}

	type target struct {
		ID    string `json:"id"`
		Label string `json:"label"`
		Name  string `json:"name"`
	}
	targets := make([]target, 0, len(rows))
	for _, row := range rows {
		m := row.AsMap()
		targets = append(targets, target{
			ID:    strVal(m["id"]),
			Label: strVal(m["label"]),
			Name:  strVal(m["name"]),
		})
	}
	return c.JSON(targets)
}

func ToggleOwned(c *fiber.Ctx) error {
	id := c.Params("id")
	ctx := context.Background()
	rows, err := database.RunWrite(ctx, database.CypherToggleOwned, map[string]any{"id": id})
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}
	owned := false
	if len(rows) > 0 {
		if v, ok := rows[0].Get("owned"); ok {
			owned, _ = v.(bool)
		}
	}
	return c.JSON(fiber.Map{"id": id, "owned": owned})
}

func GetHighValue(c *fiber.Ctx) error {
	ctx := context.Background()
	rows, err := database.RunQuery(ctx, database.CypherHighValue, nil)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": err.Error()})
	}

	type hv struct {
		ID     string `json:"id"`
		Label  string `json:"label"`
		Name   string `json:"name"`
		Reason string `json:"reason"`
	}
	results := make([]hv, 0, len(rows))
	for _, row := range rows {
		m := row.AsMap()
		results = append(results, hv{
			ID:     strVal(m["id"]),
			Label:  strVal(m["label"]),
			Name:   strVal(m["name"]),
			Reason: strVal(m["reason"]),
		})
	}
	return c.JSON(results)
}

func rowToPath(row *neo4j.Record) models.PathResult {
	m := row.AsMap()
	var result models.PathResult

	if nodes, ok := m["nodes"].([]any); ok {
		for _, n := range nodes {
			if nm, ok := n.(map[string]any); ok {
				result.Nodes = append(result.Nodes, models.PathNode{
					ID:    strVal(nm["id"]),
					Label: strVal(nm["label"]),
					Name:  strVal(nm["name"]),
				})
			}
		}
	}
	if edges, ok := m["edges"].([]any); ok {
		for _, e := range edges {
			if em, ok := e.(map[string]any); ok {
				result.Edges = append(result.Edges, models.PathEdge{
					Source: strVal(em["source"]),
					Target: strVal(em["target"]),
					Type:   strVal(em["type"]),
				})
			}
		}
	}
	return result
}

func strVal(v any) string {
	if v == nil {
		return ""
	}
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}
