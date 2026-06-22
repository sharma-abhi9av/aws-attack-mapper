package models

type Node struct {
	ID        string         `json:"id"`
	Labels    []string       `json:"labels"`
	Props     map[string]any `json:"properties"`
}

type Edge struct {
	ID      string         `json:"id"`
	Source  string         `json:"source"`
	Target  string         `json:"target"`
	RelType string         `json:"relationship"`
	Props   map[string]any `json:"properties"`
}

type GraphResponse struct {
	Nodes []Node `json:"nodes"`
	Edges []Edge `json:"edges"`
}

type Stats struct {
	Users           int              `json:"users"`
	Roles           int              `json:"roles"`
	Groups          int              `json:"groups"`
	Policies        int              `json:"policies"`
	Buckets         int              `json:"buckets"`
	Instances       int              `json:"instances"`
	SecurityGroups  int              `json:"security_groups"`
	Edges           int              `json:"edges"`
	EdgeTypes       map[string]int   `json:"edge_types"`
	HighValueTargets HighValueSummary `json:"high_value_targets"`
}

type HighValueSummary struct {
	AdminUsers   int `json:"admin_users"`
	OpenSGs      int `json:"open_security_groups"`
	PublicBuckets int `json:"public_buckets"`
	LeakyRoles   int `json:"leaky_roles"`
}

type InlinePolicy struct {
	Name     string `json:"name"`
	Document any    `json:"document"`
}

type User struct {
	ID   string `json:"id"`
	ARN  string `json:"arn"`
	Name string `json:"name"`
	Relationships UserRelations `json:"relationships"`
}

type UserRelations struct {
	MemberOf       []string       `json:"member_of"`
	HasPolicy      []string       `json:"has_policy"`
	HasInlinePolicy []InlinePolicy `json:"has_inline_policy"`
}

type Role struct {
	ID   string `json:"id"`
	ARN  string `json:"arn"`
	Name string `json:"name"`
	Relationships RoleRelations `json:"relationships"`
}

type RoleRelations struct {
	HasPolicy      []string       `json:"has_policy"`
	HasInlinePolicy []InlinePolicy `json:"has_inline_policy"`
	Trusts         []any          `json:"trusts"`
}

type Group struct {
	ID   string `json:"id"`
	ARN  string `json:"arn"`
	Name string `json:"name"`
	Relationships GroupRelations `json:"relationships"`
}

type GroupRelations struct {
	Members        []string       `json:"members"`
	HasPolicy      []string       `json:"has_policy"`
	HasInlinePolicy []InlinePolicy `json:"has_inline_policy"`
}

type Policy struct {
	ID       string `json:"id"`
	ARN      string `json:"arn"`
	Name     string `json:"name"`
	Document any    `json:"document"`
}

type S3Bucket struct {
	ID              string `json:"id"`
	ARN             string `json:"arn"`
	Name            string `json:"name"`
	Region          string `json:"region"`
	PublicAccessBlock any  `json:"public_access_block"`
	Relationships  S3Relations `json:"relationships"`
}

type S3Relations struct {
	HasPolicy any `json:"has_policy"`
}

type EC2Instance struct {
	ID             string            `json:"id"`
	Name           string            `json:"name"`
	State          string            `json:"state"`
	PublicIP       any               `json:"public_ip"`
	PrivateIP      any               `json:"private_ip"`
	InstanceType   any               `json:"instance_type"`
	KeyName        any               `json:"key_name"`
	VpcID          any               `json:"vpc_id"`
	IMDSv2Required bool              `json:"imdsv2_required"`
	Relationships  EC2Relations      `json:"relationships"`
}

type EC2Relations struct {
	HasRole       any      `json:"has_role"`
	SecurityGroups []string `json:"security_groups"`
}

type SecurityGroup struct {
	ID              string `json:"id"`
	Name            string `json:"name"`
	Description     string `json:"description"`
	VpcID           any    `json:"vpc_id"`
	HasPublicInbound bool  `json:"has_public_inbound"`
	Relationships   SGRelations `json:"relationships"`
}

type SGRelations struct {
	InboundRules  []any `json:"inbound_rules"`
	OutboundRules []any `json:"outbound_rules"`
}

type SearchResult struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Type     string `json:"type"`
	Subtitle string `json:"subtitle"`
}

type PathResult struct {
	Nodes []PathNode `json:"nodes"`
	Edges []PathEdge `json:"edges"`
}

type PathNode struct {
	ID    string `json:"id"`
	Label string `json:"label"`
	Name  string `json:"name"`
}

type PathEdge struct {
	Source string `json:"source"`
	Target string `json:"target"`
	Type   string `json:"type"`
}

type IngestProgress struct {
	Step    string `json:"step"`
	Total   int    `json:"total"`
	Created int    `json:"created"`
	Skipped int    `json:"skipped"`
	Errors  int    `json:"errors"`
	Done    bool   `json:"done"`
	Message string `json:"message,omitempty"`
}
