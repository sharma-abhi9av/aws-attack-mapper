"""
Transforms raw AWS extractor output into a standardised formatfor Neo4j ingestion.

Standard format for every entity:
    {
        "id":       unique AWS ID,
        "arn":      full ARN,
        "name":     human readable name,
        "type":     "User" | "Role" | "Group" | "Policy",
        "service":  "iam",
        "relationships": {
            "member_of":         list of ARNs (groups user belongs to)
            "has_policy":        list of ARNs (attached managed policies)
            "has_inline_policy": list of {name, document} dicts
            "trusts":            list of principals (roles only)
            "members":           list of ARNs (groups only)
        }
    }
"""

def normalize_users(users: list) -> list:
    normalised = []
    for user in users: 
        normalised.append({
            "id" : user["UserId"],
            "arn": user["Arn"],
            "name": user["UserName"], 
            "type": "User",
            "service": "iam",
            "relationships":{
                "member_of": [group["Arn"] for group in user["Groups"]],
                "has_policy": [policy["PolicyArn"] for policy in user["AttachedPolicies"]],
                "has_inline_policy": [{"name": p["PolicyName"], "document": p["Document"]} for p in user["InlinePolicies"]]
            }
        })
    return normalised
def normalize_roles(roles: list) -> list:
    normalised = []
    for role in roles: 
        normalised.append({
            "id" : role["RoleId"],
            "arn": role["Arn"],
            "name": role["RoleName"], 
            "type": "Role",
            "service": "iam",
            "relationships":{
                "has_policy": [policy["PolicyArn"] for policy in role["AttachedPolicies"]],
                "has_inline_policy": [{"name": p["PolicyName"], "document": p["Document"]} for p in role["InlinePolicies"]],
                "trusts": role["AssumeRolePolicyDocument"]["Statement"]
            }
        })
    return normalised
def normalize_groups(groups: list) -> list:
    normalised = []
    for group in groups: 
        normalised.append({
            "id" : group["GroupId"],
            "arn": group["Arn"],
            "name": group["GroupName"], 
            "type": "Group",
            "service": "iam",
            "relationships":{
                "members": [user["Arn"] for user in group["Members"]],
                "has_policy": [policy["PolicyArn"] for policy in group["AttachedPolicies"]],
                "has_inline_policy": [{"name": p["PolicyName"], "document": p["Document"]} for p in group["InlinePolicies"]]
            }
        })
    return normalised
def normalize_policies(policies: list) -> list:
    normalised = []
    for policy in policies: 
        normalised.append({
            "id" : policy["PolicyId"],
            "arn": policy["Arn"],
            "name": policy["PolicyName"], 
            "type": "Policy",
            "service": "iam",
            "document": policy.get("Document", None),
            "relationships":{}
        })
    return normalised   

def normalize_buckets(buckets: list) -> list:
    normalised = []
    for bucket in buckets:
        normalised.append({
            "id":      bucket["Name"],     # S3 buckets have no ID — name is unique
            "arn":     f"arn:aws:s3:::{bucket['Name']}",   # S3 ARN format
            "name":    bucket["Name"],
            "type":    "S3Bucket",
            "service": "s3",
            "region":  bucket.get("Region", "us-east-1"),
            "public_access_block": bucket.get("PublicAccessBlock", None),
            "relationships": {
                "has_policy": bucket.get("Policy", None)
            }
        })
    return normalised