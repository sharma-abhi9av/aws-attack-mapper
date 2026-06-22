package database

const (
	// ─── Stats ──────────────────────────────────────
	CypherStats = `
		MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count
	`

	CypherEdgeCount = `
		MATCH ()-[r]->() RETURN count(r) AS count
	`

	CypherEdgeTypes = `
		MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS cnt ORDER BY cnt DESC
	`

	CypherAdminUsers = `
		MATCH (u:User)-[:HAS_POLICY]->(p:Policy)
		WHERE p.arn CONTAINS 'AdministratorAccess'
		RETURN count(DISTINCT u) AS c
	`

	CypherOpenSGs = `
		MATCH (sg:SecurityGroup)
		WHERE sg.has_public_inbound = true
		RETURN count(sg) AS c
	`

	CypherPublicBuckets = `
		MATCH (b:S3Bucket)
		WHERE b.public_access_block IS NULL
		   OR (b.public_access_block.BlockPublicAcls = false
		   AND b.public_access_block.BlockPublicPolicy = false)
		RETURN count(b) AS c
	`

	CypherLeakyRoles = `
		MATCH (r:Role)
		WHERE r.trusts CONTAINS '"AWS":"*"' OR r.trusts CONTAINS '"AWS": "*"'
		RETURN count(r) AS c
	`

	// ─── Nodes ──────────────────────────────────────
	CypherAllNodes = `
		MATCH (n:$LABEL)
		RETURN n.id AS id, n.name AS name, n.arn AS arn
		ORDER BY n.name
	`

	CypherNodeByID = `
		MATCH (n {id: $id})
		RETURN labels(n) AS labels, properties(n) AS props
		LIMIT 1
	`

	// ─── Graph ──────────────────────────────────────
	CypherNeighbors = `
		MATCH (n {id: $id})-[r]-(connected)
		RETURN connected.id AS id,
		       labels(connected)[0] AS label,
		       connected.name AS name,
		       connected.arn AS arn,
		       connected.owned AS owned,
		       type(r) AS relType,
		       id(r) AS relId,
		       properties(r) AS relProps,
		       CASE WHEN startNode(r).id = $id THEN 'out' ELSE 'in' END AS direction
	`

	CypherShortestPath = `
		MATCH path = shortestPath(
			(start {id: $from})-[*1..$MAXDEPTH]-(end {id: $to})
		)
		WHERE start IS NOT NULL AND end IS NOT NULL
		RETURN [n IN nodes(path) | {id: n.id, label: labels(n)[0], name: n.name}] AS nodes,
		       [r IN relationships(path) | {source: startNode(r).id, target: endNode(r).id, type: type(r)}] AS edges
	`

	CypherAllPaths = `
		MATCH path = (start {id: $from})-[*1..$MAXDEPTH]-(end {id: $to})
		WHERE start IS NOT NULL AND end IS NOT NULL
		RETURN [n IN nodes(path) | {id: n.id, label: labels(n)[0], name: n.name}] AS nodes,
		       [r IN relationships(path) | {source: startNode(r).id, target: endNode(r).id, type: type(r)}] AS edges
		LIMIT 50
	`

	CypherReachable = `
		MATCH (start {id: $id})-[*1..$MAXDEPTH]->(target)
		WHERE start IS NOT NULL
		RETURN DISTINCT target.id AS id,
		       labels(target)[0] AS label,
		       target.name AS name
		LIMIT 200
	`

	CypherHighValue = `
		MATCH (n)
		WHERE
			(n:User AND EXISTS {
				MATCH (n)-[:HAS_POLICY]->(p:Policy)
				WHERE p.arn CONTAINS 'AdministratorAccess'
			})
			OR (n:SecurityGroup AND n.has_public_inbound = true)
			OR (n:S3Bucket AND n.public_access_block IS NULL)
			OR (n:Role AND n.name CONTAINS 'Leaky')
		RETURN n.id AS id, labels(n)[0] AS label, n.name AS name,
		       CASE
		           WHEN n.has_public_inbound = true THEN 'Public inbound rule'
		           WHEN n.public_access_block IS NULL THEN 'No public access block'
		           WHEN n.name CONTAINS 'Leaky' THEN 'Leaky trust policy'
		           ELSE 'AdministratorAccess'
		       END AS reason
	`

	CypherSearch = `
		MATCH (n)
		WHERE n.name CONTAINS $q OR n.id CONTAINS $q OR n.arn CONTAINS $q
		RETURN n.id AS id, n.name AS name, labels(n)[0] AS label, n.arn AS arn
		LIMIT 50
	`

	// ─── Owned ─────────────────────────────────────
	CypherToggleOwned = `
		MATCH (n {id: $id})
		SET n.owned = CASE WHEN n.owned IS NULL OR n.owned = false THEN true ELSE false END
		RETURN n.owned AS owned
	`

	CypherUnsetOwned = `
		MATCH (n {id: $id})
		REMOVE n.owned
	`

	// ─── Full Graph ────────────────────────────────
	CypherAllNodesFull = `
		MATCH (n)
		RETURN n.id AS id, labels(n) AS labels, properties(n) AS props
	`

	CypherAllEdges = `
		MATCH (s)-[r]->(t)
		RETURN id(r) AS id, s.id AS source, t.id AS target, type(r) AS relType
	`
)
