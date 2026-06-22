package ingest

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/anomalyco/mooaws/api/database"
)

type Ingestor struct {
	OutputDir string
}

func New(outputDir string) *Ingestor {
	return &Ingestor{OutputDir: outputDir}
}

func (ig *Ingestor) Run(ctx context.Context) error {
	if err := ig.deleteAll(ctx); err != nil {
		return err
	}
	if err := ig.ingestPolicies(ctx); err != nil {
		return err
	}
	if err := ig.ingestUsers(ctx); err != nil {
		return err
	}
	if err := ig.ingestRoles(ctx); err != nil {
		return err
	}
	if err := ig.ingestGroups(ctx); err != nil {
		return err
	}
	if err := ig.ingestBuckets(ctx); err != nil {
		return err
	}
	if err := ig.ingestSecurityGroups(ctx); err != nil {
		return err
	}
	if err := ig.ingestEC2(ctx); err != nil {
		return err
	}
	if err := ig.inferEdges(ctx); err != nil {
		log.Printf("[ingest] infer edges warning: %v", err)
	}
	return nil
}

func (ig *Ingestor) deleteAll(ctx context.Context) error {
	_, err := database.RunWrite(ctx, "MATCH (n) DETACH DELETE n", nil)
	return err
}

// ─── helpers ──────────────────────────────────────

func readJSON(path string, dest any) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	return json.NewDecoder(f).Decode(dest)
}

func resolvePath(dir, filename string) string {
	return filepath.Join(dir, filename)
}

func execMerge(ctx context.Context, cypher string, params map[string]any) error {
	_, err := database.RunWrite(ctx, cypher, params)
	if err != nil {
		return err
	}
	return nil
}


// ─── Policies ──────────────────────────────────────

type rawPolicy struct {
	ID       string `json:"id"`
	ARN      string `json:"arn"`
	Name     string `json:"name"`
	Document any    `json:"document"`
}

func (ig *Ingestor) ingestPolicies(ctx context.Context) error {
	var policies []rawPolicy
	if err := readJSON(resolvePath(ig.OutputDir, "policies.json"), &policies); err != nil {
		return fmt.Errorf("policies: %w", err)
	}
	for _, p := range policies {
		docJSON, _ := json.Marshal(p.Document)
		cypher := `
			MERGE (n:Policy {id: $id})
			SET n.arn = $arn, n.name = $name, n.document = $document
		`
		if err := execMerge(ctx, cypher, map[string]any{
			"id":       p.ID,
			"arn":      p.ARN,
			"name":     p.Name,
			"document": string(docJSON),
		}); err != nil {
			log.Printf("[ingest] policy %s: %v", p.Name, err)
		}
	}
	log.Printf("[ingest] policies: %d created", len(policies))
	return nil
}

// ─── Users ─────────────────────────────────────────

type rawUsers []struct {
	ID   string `json:"id"`
	ARN  string `json:"arn"`
	Name string `json:"name"`
	Relationships struct {
		MemberOf       []string           `json:"member_of"`
		HasPolicy      []string           `json:"has_policy"`
		HasInlinePolicy []json.RawMessage `json:"has_inline_policy"`
	} `json:"relationships"`
}

func (ig *Ingestor) ingestUsers(ctx context.Context) error {
	var users rawUsers
	if err := readJSON(resolvePath(ig.OutputDir, "users.json"), &users); err != nil {
		return fmt.Errorf("users: %w", err)
	}
	for _, u := range users {
		cypher := `
			MERGE (n:User {id: $id})
			SET n.arn = $arn, n.name = $name
		`
		if err := execMerge(ctx, cypher, map[string]any{
			"id": u.ID, "arn": u.ARN, "name": u.Name,
		}); err != nil {
			log.Printf("[ingest] user %s: %v", u.Name, err)
			continue
		}
		for _, groupARN := range u.Relationships.MemberOf {
			execMerge(ctx, `
				MATCH (u:User {id: $uid})
				MERGE (g:Group {arn: $garn})
				MERGE (u)-[:MEMBER_OF]->(g)
			`, map[string]any{"uid": u.ID, "garn": groupARN})
		}
		for _, policyARN := range u.Relationships.HasPolicy {
			execMerge(ctx, `
				MATCH (u:User {id: $uid})
				MERGE (p:Policy {arn: $parn})
				MERGE (u)-[:HAS_POLICY]->(p)
			`, map[string]any{"uid": u.ID, "parn": policyARN})
		}
		for _, rawIP := range u.Relationships.HasInlinePolicy {
			var ip struct {
				Name     string `json:"name"`
				Document any    `json:"document"`
			}
			if json.Unmarshal(rawIP, &ip) != nil {
				continue
			}
			docJSON, _ := json.Marshal(ip.Document)
			execMerge(ctx, `
				MATCH (u:User {id: $uid})
				CREATE (u)-[:HAS_INLINE_POLICY]->(:InlinePolicy {
					id: $uid + '_' + $pname,
					name: $pname,
					document: $document
				})
			`, map[string]any{"uid": u.ID, "pname": ip.Name, "document": string(docJSON)})
		}
	}
	log.Printf("[ingest] users: %d created", len(users))
	return nil
}

// ─── Roles ─────────────────────────────────────────

type rawRoles []struct {
	ID   string `json:"id"`
	ARN  string `json:"arn"`
	Name string `json:"name"`
	Relationships struct {
		HasPolicy      []string           `json:"has_policy"`
		HasInlinePolicy []json.RawMessage `json:"has_inline_policy"`
		Trusts         []any              `json:"trusts"`
	} `json:"relationships"`
}

func (ig *Ingestor) ingestRoles(ctx context.Context) error {
	var roles rawRoles
	if err := readJSON(resolvePath(ig.OutputDir, "roles.json"), &roles); err != nil {
		return fmt.Errorf("roles: %w", err)
	}
	for _, r := range roles {
		trustsJSON, _ := json.Marshal(r.Relationships.Trusts)
		cypher := `
			MERGE (n:Role {id: $id})
			SET n.arn = $arn, n.name = $name, n.trusts = $trusts
		`
		if err := execMerge(ctx, cypher, map[string]any{
			"id": r.ID, "arn": r.ARN, "name": r.Name, "trusts": string(trustsJSON),
		}); err != nil {
			log.Printf("[ingest] role %s: %v", r.Name, err)
			continue
		}
		for _, policyARN := range r.Relationships.HasPolicy {
			execMerge(ctx, `
				MATCH (r:Role {id: $rid})
				MERGE (p:Policy {arn: $parn})
				MERGE (r)-[:HAS_POLICY]->(p)
			`, map[string]any{"rid": r.ID, "parn": policyARN})
		}
		for _, rawIP := range r.Relationships.HasInlinePolicy {
			var ip struct {
				Name     string `json:"name"`
				Document any    `json:"document"`
			}
			if json.Unmarshal(rawIP, &ip) != nil {
				continue
			}
			docJSON, _ := json.Marshal(ip.Document)
			execMerge(ctx, `
				MATCH (r:Role {id: $rid})
				CREATE (r)-[:HAS_INLINE_POLICY]->(:InlinePolicy {
					id: $rid + '_' + $pname,
					name: $pname,
					document: $document
				})
			`, map[string]any{"rid": r.ID, "pname": ip.Name, "document": string(docJSON)})
		}
	}
	log.Printf("[ingest] roles: %d created", len(roles))
	return nil
}

// ─── Groups ────────────────────────────────────────

type rawGroups []struct {
	ID   string `json:"id"`
	ARN  string `json:"arn"`
	Name string `json:"name"`
	Relationships struct {
		Members        []string           `json:"members"`
		HasPolicy      []string           `json:"has_policy"`
		HasInlinePolicy []json.RawMessage `json:"has_inline_policy"`
	} `json:"relationships"`
}

func (ig *Ingestor) ingestGroups(ctx context.Context) error {
	var groups rawGroups
	if err := readJSON(resolvePath(ig.OutputDir, "groups.json"), &groups); err != nil {
		return fmt.Errorf("groups: %w", err)
	}
	for _, g := range groups {
		cypher := `
			MERGE (n:Group {id: $id})
			SET n.arn = $arn, n.name = $name
		`
		if err := execMerge(ctx, cypher, map[string]any{
			"id": g.ID, "arn": g.ARN, "name": g.Name,
		}); err != nil {
			log.Printf("[ingest] group %s: %v", g.Name, err)
			continue
		}
		for _, memberARN := range g.Relationships.Members {
			execMerge(ctx, `
				MATCH (g:Group {id: $gid})
				MERGE (u:User {arn: $uarn})
				MERGE (u)-[:MEMBER_OF]->(g)
			`, map[string]any{"gid": g.ID, "uarn": memberARN})
		}
		for _, policyARN := range g.Relationships.HasPolicy {
			execMerge(ctx, `
				MATCH (g:Group {id: $gid})
				MERGE (p:Policy {arn: $parn})
				MERGE (g)-[:HAS_POLICY]->(p)
			`, map[string]any{"gid": g.ID, "parn": policyARN})
		}
	}
	log.Printf("[ingest] groups: %d created", len(groups))
	return nil
}

// ─── S3 Buckets ────────────────────────────────────

type rawBuckets []struct {
	ID              string `json:"id"`
	ARN             string `json:"arn"`
	Name            string `json:"name"`
	Region          string `json:"region"`
	PublicAccessBlock any  `json:"public_access_block"`
	Relationships  struct {
		HasPolicy any `json:"has_policy"`
	} `json:"relationships"`
}

func (ig *Ingestor) ingestBuckets(ctx context.Context) error {
	var buckets rawBuckets
	if err := readJSON(resolvePath(ig.OutputDir, "s3_buckets.json"), &buckets); err != nil {
		return fmt.Errorf("buckets: %w", err)
	}
	for _, b := range buckets {
		pabJSON, _ := json.Marshal(b.PublicAccessBlock)
		policyJSON, _ := json.Marshal(b.Relationships.HasPolicy)
		cypher := `
			MERGE (n:S3Bucket {id: $id})
			SET n.arn = $arn, n.name = $name, n.region = $region,
			    n.public_access_block = $pab
		`
		if err := execMerge(ctx, cypher, map[string]any{
			"id": b.ID, "arn": b.ARN, "name": b.Name,
			"region": b.Region, "pab": string(pabJSON),
		}); err != nil {
			log.Printf("[ingest] bucket %s: %v", b.Name, err)
			continue
		}
		if policyJSON != nil && string(policyJSON) != "null" {
			execMerge(ctx, `
				MATCH (b:S3Bucket {id: $bid})
				MERGE (bp:BucketPolicy {id: $bid + '_policy'})
				SET bp.document = $doc
				MERGE (b)-[:HAS_POLICY]->(bp)
			`, map[string]any{"bid": b.ID, "doc": string(policyJSON)})
		}
	}
	log.Printf("[ingest] buckets: %d created", len(buckets))
	return nil
}

// ─── Security Groups ───────────────────────────────

type rawSG struct {
	ID              string `json:"id"`
	Name            string `json:"name"`
	Description     string `json:"description"`
	VpcID           any    `json:"vpc_id"`
	HasPublicInbound bool  `json:"has_public_inbound"`
	Relationships  struct {
		InboundRules  json.RawMessage `json:"inbound_rules"`
		OutboundRules json.RawMessage `json:"outbound_rules"`
	} `json:"relationships"`
}

func (ig *Ingestor) ingestSecurityGroups(ctx context.Context) error {
	var sgs []rawSG
	if err := readJSON(resolvePath(ig.OutputDir, "security_groups.json"), &sgs); err != nil {
		return fmt.Errorf("security_groups: %w", err)
	}
	for _, sg := range sgs {
		inJSON, _ := json.Marshal(sg.Relationships.InboundRules)
		outJSON, _ := json.Marshal(sg.Relationships.OutboundRules)
		cypher := `
			MERGE (n:SecurityGroup {id: $id})
			SET n.name = $name, n.description = $desc,
			    n.vpc_id = $vpc, n.has_public_inbound = $public,
			    n.inbound_rules = $inbound, n.outbound_rules = $outbound
		`
		execMerge(ctx, cypher, map[string]any{
			"id": sg.ID, "name": sg.Name, "desc": sg.Description,
			"vpc": sg.VpcID, "public": sg.HasPublicInbound,
			"inbound": string(inJSON), "outbound": string(outJSON),
		})
	}
	log.Printf("[ingest] security groups: %d created", len(sgs))
	return nil
}

// ─── EC2 Instances ─────────────────────────────────

type rawEC2 struct {
	ID             string `json:"id"`
	Name           string `json:"name"`
	State          string `json:"state"`
	PublicIP       any    `json:"public_ip"`
	PrivateIP      any    `json:"private_ip"`
	InstanceType   any    `json:"instance_type"`
	KeyName        any    `json:"key_name"`
	VpcID          any    `json:"vpc_id"`
	IMDSv2Required bool   `json:"imdsv2_required"`
	Relationships struct {
		HasRole       any      `json:"has_role"`
		SecurityGroups []string `json:"security_groups"`
	} `json:"relationships"`
}

func (ig *Ingestor) ingestEC2(ctx context.Context) error {
	var instances []rawEC2
	if err := readJSON(resolvePath(ig.OutputDir, "ec2_instances.json"), &instances); err != nil {
		return fmt.Errorf("ec2_instances: %w", err)
	}
	for _, inst := range instances {
		cypher := `
			MERGE (n:EC2Instance {id: $id})
			SET n.name = $name, n.state = $state,
			    n.public_ip = $pub, n.private_ip = $priv,
			    n.instance_type = $type, n.key_name = $key,
			    n.vpc_id = $vpc, n.imdsv2_required = $imds
		`
		if err := execMerge(ctx, cypher, map[string]any{
			"id": inst.ID, "name": inst.Name, "state": inst.State,
			"pub": inst.PublicIP, "priv": inst.PrivateIP,
			"type": inst.InstanceType, "key": inst.KeyName,
			"vpc": inst.VpcID, "imds": inst.IMDSv2Required,
		}); err != nil {
			log.Printf("[ingest] ec2 %s: %v", inst.Name, err)
			continue
		}
		for _, sgID := range inst.Relationships.SecurityGroups {
			execMerge(ctx, `
				MATCH (e:EC2Instance {id: $eid})
				MERGE (sg:SecurityGroup {id: $sgid})
				MERGE (e)-[:USES_SG]->(sg)
			`, map[string]any{"eid": inst.ID, "sgid": sgID})
		}
		if inst.Relationships.HasRole != nil {
			roleARN := fmt.Sprintf("%v", inst.Relationships.HasRole)
			execMerge(ctx, `
				MATCH (e:EC2Instance {id: $eid})
				MERGE (r:Role {arn: $rarn})
				MERGE (e)-[:HAS_ROLE]->(r)
			`, map[string]any{"eid": inst.ID, "rarn": roleARN})
		}
	}
	log.Printf("[ingest] ec2 instances: %d created", len(instances))
	return nil
}

// ─── Inferred GRANTS_ACCESS edges ──────────────────

type iamStatement struct {
	Effect   string `json:"Effect"`
	Action   any    `json:"Action"`
	Resource any    `json:"Resource"`
}

type iamDoc struct {
	Statement any `json:"Statement"`
}

func toSlice(v any) []string {
	switch val := v.(type) {
	case string:
		return []string{val}
	case []any:
		s := make([]string, 0, len(val))
		for _, item := range val {
			if str, ok := item.(string); ok {
				s = append(s, str)
			}
		}
		return s
	}
	return nil
}

func actionsMatch(actions []string, prefix string) bool {
	for _, a := range actions {
		if a == "*" || a == prefix+":*" || strings.HasPrefix(a, prefix+":") {
			return true
		}
	}
	return false
}

func resourceIsAll(resources []string) bool {
	for _, r := range resources {
		if r == "*" || r == "arn:aws:s3:::*" || r == "arn:aws:ec2:*" || r == "arn:aws:*" {
			return true
		}
	}
	return false
}

func resourceMatchesBucket(resources []string) string {
	for _, r := range resources {
		// arn:aws:s3:::bucket-name or arn:aws:s3:::bucket-name/*
		if strings.HasPrefix(r, "arn:aws:s3:::") {
			name := strings.TrimPrefix(r, "arn:aws:s3:::")
			name = strings.TrimSuffix(name, "/*")
			name = strings.TrimSuffix(name, "/")
			return name
		}
	}
	return ""
}

func (ig *Ingestor) inferEdges(ctx context.Context) error {
	// Collect all S3 bucket IDs & names for matching
	bucketRows, err := database.RunQuery(ctx, "MATCH (b:S3Bucket) RETURN b.id AS id, b.name AS name", nil)
	if err != nil {
		return fmt.Errorf("query buckets: %w", err)
	}
	type bucketInfo struct{ id, name string }
	var buckets []bucketInfo
	for _, r := range bucketRows {
		m := r.AsMap()
		id, _ := m["id"].(string)
		name, _ := m["name"].(string)
		if id != "" {
			buckets = append(buckets, bucketInfo{id, name})
		}
	}

	// Collect all EC2 instance IDs
	ec2Rows, err := database.RunQuery(ctx, "MATCH (e:EC2Instance) RETURN e.id AS id", nil)
	if err != nil {
		return fmt.Errorf("query ec2: %w", err)
	}
	var ec2IDs []string
	for _, r := range ec2Rows {
		m := r.AsMap()
		id, _ := m["id"].(string)
		if id != "" {
			ec2IDs = append(ec2IDs, id)
		}
	}

	// Process all Policy + InlinePolicy nodes with documents
	docRows, err := database.RunQuery(ctx, `
		MATCH (n)
		WHERE (n:Policy OR n:InlinePolicy)
		      AND n.document IS NOT NULL
		RETURN n.id AS id, n.document AS doc
	`, nil)
	if err != nil {
		return fmt.Errorf("query policy docs: %w", err)
	}

	var edgeCount int
	for _, row := range docRows {
		m := row.AsMap()
		pid, _ := m["id"].(string)
		docStr, _ := m["doc"].(string)
		if pid == "" || docStr == "" {
			continue
		}

		var doc iamDoc
		if err := json.Unmarshal([]byte(docStr), &doc); err != nil {
			continue
		}

		var statements []iamStatement
		switch s := doc.Statement.(type) {
		case map[string]any:
			var stmt iamStatement
			stmt.Effect, _ = s["Effect"].(string)
			stmt.Action = s["Action"]
			stmt.Resource = s["Resource"]
			statements = append(statements, stmt)
		case []any:
			for _, item := range s {
				if sm, ok := item.(map[string]any); ok {
					var stmt iamStatement
					stmt.Effect, _ = sm["Effect"].(string)
					stmt.Action = sm["Action"]
					stmt.Resource = sm["Resource"]
					statements = append(statements, stmt)
				}
			}
		}

		for _, stmt := range statements {
			if stmt.Effect != "Allow" {
				continue
			}
			actions := toSlice(stmt.Action)
			resources := toSlice(stmt.Resource)
			if len(actions) == 0 || len(resources) == 0 {
				continue
			}

			hasS3 := actionsMatch(actions, "s3")
			hasEC2 := actionsMatch(actions, "ec2")
			allResources := resourceIsAll(resources)

			// GRANTS_ACCESS to S3 buckets
			if hasS3 {
				if allResources {
					// Grant to ALL buckets
					for _, b := range buckets {
						database.RunWrite(ctx, `
							MERGE (p {id: $pid})
							MERGE (b:S3Bucket {id: $bid})
							MERGE (p)-[:GRANTS_ACCESS]->(b)
						`, map[string]any{"pid": pid, "bid": b.id})
						edgeCount++
					}
				} else {
					// Match specific buckets by name
					bucketName := resourceMatchesBucket(resources)
					if bucketName != "" {
						for _, b := range buckets {
							if b.name == bucketName || strings.Contains(b.id, bucketName) {
								database.RunWrite(ctx, `
									MERGE (p {id: $pid})
									MERGE (b:S3Bucket {id: $bid})
									MERGE (p)-[:GRANTS_ACCESS]->(b)
								`, map[string]any{"pid": pid, "bid": b.id})
								edgeCount++
							}
						}
					}
				}
			}

			// GRANTS_ACCESS to EC2 instances
			if hasEC2 && allResources {
				for _, eid := range ec2IDs {
					database.RunWrite(ctx, `
						MERGE (p {id: $pid})
						MERGE (e:EC2Instance {id: $eid})
						MERGE (p)-[:GRANTS_ACCESS]->(e)
					`, map[string]any{"pid": pid, "eid": eid})
					edgeCount++
				}
			}
		}
	}

	log.Printf("[ingest] inferred %d GRANTS_ACCESS edges", edgeCount)
	return nil
}

