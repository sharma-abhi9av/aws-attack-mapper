# MooAWS Comprehensive Lab

AWS environment on **floci** for testing MooAWS

## Resource Inventory

### IAM Users (4)
| User | Managed Policies | Inline Policies | Groups |
|------|-----------------|-----------------|--------|
| `Bob-admin` | AdministratorAccess | — | — |
| `Alice-dev` | — | DevCustomInline (ec2:RunInstances t2.micro) | DeveloperGroup |
| `Dave-s3` | — | — | S3Team |
| `Eve-audit` | SecurityAudit | AuditStorage (s3 Put/Get) | AuditTeam |

### IAM Groups (3)
| Group | Attached Policies | Members | 
|-------|------------------|---------|
| `DeveloperGroup` | DeveloperPolicy (custom) | Alice-dev |
| `S3Team` | AmazonS3FullAccess | Dave-s3 |
| `AuditTeam` | AuditReportPolicy (custom) | Eve-audit |

### IAM Roles (3)
| Role | Trust Policy | Attached Policies | Inline |
|------|-------------|------------------|--------|
| `LeakyRole` | `Principal: "*"` (any account) | AdministratorAccess | — |
| `EC2-S3-ReadRole` | `Service: ec2.amazonaws.com` | AmazonS3ReadOnlyAccess | — |
| `Lambda-AdminRole` | `Service: lambda.amazonaws.com` | AdministratorAccess | InlineKMSPolicy |

### Custom Policies (3)
`DeveloperPolicy`, `S3FullAccessPolicy`, `AuditReportPolicy`

### S3 Buckets (5)
| Bucket | Public Policy | Public Access Block | Notes |
|--------|--------------|-------------------|-------|
| `public-read-lab` | s3:GetObject by `*` | None | Open read |
| `public-write-lab` | s3:PutObject by `*` | None | Open write |
| `confidential-data` | EC2-S3-ReadRole only | Fully blocked | Restricted |
| `logs-bucket` | None | Fully blocked | No public access |
| `audit-reports` | Eve-audit only | Fully blocked | Restricted |

### Security Groups (4)
| Group | Inbound Rules | Public? |
|-------|--------------|---------|
| `SSH-Open-World` | TCP/22 from `0.0.0.0/0` | Yes |
| `RDP-Open-World` | TCP/3389 from `0.0.0.0/0` | Yes |
| `WebSG` | TCP/80,443 from `0.0.0.0/0` | Yes |
| `InternalSG` | All traffic from RFC1918 | No |

### EC2 Instances (3)
| Instance | Security Group | IAM Profile | Notes |
|----------|---------------|-------------|-------|
| `WebServer-01` | WebSG | — | Public web server |
| `BastionHost` | SSH-Open-World | EC2-S3-ReadRole | SSH + S3 access |
| `Database-01` | InternalSG | — | Internal only |

## Quick Start

```bash
floci start
python3 lab/setup.py
python3 main.py --endpoint-url http://localhost.floci.io:4566 2>&1
```

To see the JSON output for any resource:

```bash
cat output/users.json | python3 -m json.tool
cat output/roles.json | python3 -m json.tool
cat output/groups.json | python3 -m json.tool
cat output/policies.json | python3 -m json.tool
cat output/s3_buckets.json | python3 -m json.tool
cat output/ec2_instances.json | python3 -m json.tool
cat output/security_groups.json | python3 -m json.tool
```

## Cleanup

```bash
eval $(floci env)
python3 lab/teardown.py
floci stop
```
