"""
MooAWS Vulnerable Lab — Comprehensive
Creates a realistic AWS environment on floci with interconnected IAM, S3,
and EC2 resources for testing MooAWS attack-path enumeration.
"""

import json
import os

import boto3
from botocore.exceptions import ClientError

ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "http://localhost.floci.io:4566")
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ACCOUNT_ID = "000000000000"
KW = dict(
    endpoint_url=ENDPOINT_URL,
    region_name=REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test",
)
AWS_PREFIX = "arn:aws:iam::aws:policy"


def sts():
    return boto3.client("sts", **KW)


def iam():
    return boto3.client("iam", **KW)


def s3():
    return boto3.client("s3", **KW)


def ec2():
    return boto3.client("ec2", **KW)


def ec2_resource():
    return boto3.resource("ec2", **KW)


def p(name, **kw):
    return {"PolicyName": name, **kw}


def managed(arn):
    return {"PolicyArn": arn}


def tag(key, value):
    return {"Key": key, "Value": value}




CUSTOM_POLICIES = {
    "DeveloperPolicy": {
        "PolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "ec2:Describe*", "Resource": "*"},
                {
                    "Effect": "Allow",
                    "Action": "s3:ListBucket",
                    "Resource": "arn:aws:s3:::dev-*",
                },
                {
                    "Effect": "Allow",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::dev-*/*",
                },
            ],
        },
        "Description": "Developer read-only access to EC2 and dev S3 buckets",
    },
    "S3FullAccessPolicy": {
        "PolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "s3:*", "Resource": "*"},
            ],
        },
        "Description": "Full S3 access",
    },
    "AuditReportPolicy": {
        "PolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:GenerateCredentialReport",
                        "iam:GetCredentialReport",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3:PutObject", "s3:GetObject"],
                    "Resource": "arn:aws:s3:::audit-reports/*",
                },
            ],
        },
        "Description": "Generate and store audit reports",
    },
}


def create_customer_policies():
    print("[1] Creating customer-managed policies ...")
    c = iam()
    arns = {}
    for name, body in CUSTOM_POLICIES.items():
        try:
            resp = c.create_policy(
                PolicyName=name,
                PolicyDocument=json.dumps(body["PolicyDocument"]),
                Description=body["Description"],
            )
            arns[name] = resp["Policy"]["Arn"]
            print(f"    -> Policy '{name}' created")
        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                resp = c.list_policies(Scope="Local", MaxItems=1000)
                for p_ in resp["Policies"]:
                    if p_["PolicyName"] == name:
                        arns[name] = p_["Arn"]
                        break
                print(f"    -> Policy '{name}' already exists")
            else:
                print(f"    -> Policy '{name}' FAILED: {e}")
    return arns



USERS = [
    {
        "name": "Bob-admin",
        "managed": [f"{AWS_PREFIX}/AdministratorAccess"],
        "inline": [],
        "groups": [],
        "desc": "Full admin rights — over-privileged user",
    },
    {
        "name": "Alice-dev",
        "managed": [],
        "inline": [
            p(
                "DevCustomInline",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "ec2:RunInstances",
                            "Resource": "*",
                            "Condition": {
                                "StringEquals": {"ec2:InstanceType": "t2.micro"}
                            },
                        }
                    ],
                },
            )
        ],
        "groups": ["DeveloperGroup"],
        "desc": "Developer with EC2 run-instances restricted to t2.micro",
    },
    {
        "name": "Dave-s3",
        "managed": [],
        "inline": [],
        "groups": ["S3Team"],
        "desc": "S3 team member — full S3 access via group",
    },
    {
        "name": "Eve-audit",
        "managed": [f"{AWS_PREFIX}/ReadOnlyAccess"],
        "inline": [
            p(
                "AuditStorage",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:PutObject", "s3:GetObject"],
                            "Resource": "arn:aws:s3:::audit-reports/*",
                        },
                    ],
                },
            )
        ],
        "groups": ["AuditTeam"],
        "desc": "Auditor with ReadOnlyAccess + inline audit storage policy",
    },
]


def create_users():
    print("[2] Creating IAM users with policies ...")
    c = iam()
    for u in USERS:
        try:
            c.create_user(UserName=u["name"])
            c.create_access_key(UserName=u["name"])
            for m in u["managed"]:
                c.attach_user_policy(UserName=u["name"], PolicyArn=m)
            for ip in u["inline"]:
                c.put_user_policy(
                    UserName=u["name"],
                    PolicyName=ip["PolicyName"],
                    PolicyDocument=json.dumps(ip["PolicyDocument"]),
                )
            print(f"    -> User '{u['name']}' created — {u['desc']}")
        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                print(f"    -> User '{u['name']}' already exists")
            else:
                print(f"    -> User '{u['name']}' FAILED: {e}")



GROUPS = [
    {
        "name": "DeveloperGroup",
        "managed": [],  # attached via custom policy below
        "inline": [],
        "members": ["Alice-dev"],
        "custom_policies": ["DeveloperPolicy"],
        "desc": "Developers with EC2/S3 read access",
    },
    {
        "name": "S3Team",
        "managed": [f"{AWS_PREFIX}/AmazonS3FullAccess"],
        "inline": [],
        "members": ["Dave-s3"],
        "custom_policies": [],
        "desc": "S3 team with full S3 access",
    },
    {
        "name": "AuditTeam",
        "managed": [],
        "inline": [],
        "members": ["Eve-audit"],
        "custom_policies": ["AuditReportPolicy"],
        "desc": "Audit team with reporting access",
    },
]


def create_groups(custom_policy_arns):
    print("[3] Creating IAM groups ...")
    c = iam()
    for g in GROUPS:
        try:
            c.create_group(GroupName=g["name"])
            for m in g["managed"]:
                c.attach_group_policy(GroupName=g["name"], PolicyArn=m)
            for cp in g["custom_policies"]:
                arn = custom_policy_arns.get(cp)
                if arn:
                    c.attach_group_policy(GroupName=g["name"], PolicyArn=arn)
            for ip in g["inline"]:
                c.put_group_policy(
                    GroupName=g["name"],
                    PolicyName=ip["PolicyName"],
                    PolicyDocument=json.dumps(ip["PolicyDocument"]),
                )
            for member in g["members"]:
                c.add_user_to_group(GroupName=g["name"], UserName=member)
            print(f"    -> Group '{g['name']}' created — {g['desc']}")
        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                print(f"    -> Group '{g['name']}' already exists")
            else:
                print(f"    -> Group '{g['name']}' FAILED: {e}")



ROLES = [
    {
        "name": "LeakyRole",
        "trust": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
        "managed": [f"{AWS_PREFIX}/AdministratorAccess"],
        "inline": [],
        "desc": "ANY AWS account can assume — full admin",
    },
    {
        "name": "EC2-S3-ReadRole",
        "trust": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
        "managed": [f"{AWS_PREFIX}/AmazonS3ReadOnlyAccess"],
        "inline": [],
        "desc": "EC2 instances can assume — S3 read-only",
    },
    {
        "name": "Lambda-AdminRole",
        "trust": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
        "managed": [f"{AWS_PREFIX}/AdministratorAccess"],
        "inline": [
            p(
                "InlineKMSPolicy",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": "kms:Decrypt", "Resource": "*"},
                    ],
                },
            )
        ],
        "desc": "Lambda can assume — admin + KMS decrypt inline",
    },
]


def create_roles():
    print("[4] Creating IAM roles ...")
    c = iam()
    for r in ROLES:
        try:
            c.create_role(
                RoleName=r["name"],
                AssumeRolePolicyDocument=json.dumps(r["trust"]),
                Description=r["desc"],
            )
            for m in r["managed"]:
                c.attach_role_policy(RoleName=r["name"], PolicyArn=m)
            for ip in r["inline"]:
                c.put_role_policy(
                    RoleName=r["name"],
                    PolicyName=ip["PolicyName"],
                    PolicyDocument=json.dumps(ip["PolicyDocument"]),
                )
            print(f"    -> Role '{r['name']}' created — {r['desc']}")
        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                print(f"    -> Role '{r['name']}' already exists")
            else:
                print(f"    -> Role '{r['name']}' FAILED: {e}")


BUCKETS = [
    {
        "name": "public-read-lab",
        "policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::public-read-lab/*",
                }
            ],
        },
        "block": {
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        },
        "desc": "Anyone can READ objects — no public access block",
    },
    {
        "name": "public-write-lab",
        "policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:PutObject",
                    "Resource": "arn:aws:s3:::public-write-lab/*",
                }
            ],
        },
        "block": None,
        "desc": "Anyone can WRITE objects — no public access block at all",
    },
    {
        "name": "confidential-data",
        "policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{ACCOUNT_ID}:role/EC2-S3-ReadRole"
                    },
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::confidential-data/*",
                }
            ],
        },
        "block": {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
        "desc": "Restricted — only EC2-S3-ReadRole can read, public access blocked",
    },
    {
        "name": "logs-bucket",
        "policy": None,
        "block": {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
        "desc": "Log storage — no bucket policy, public access fully blocked",
    },
    {
        "name": "audit-reports",
        "policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT_ID}:user/Eve-audit"},
                    "Action": ["s3:PutObject", "s3:GetObject"],
                    "Resource": "arn:aws:s3:::audit-reports/*",
                }
            ],
        },
        "block": {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
        "desc": "Audit reports — only Eve-audit can read/write",
    },
]


def create_buckets():
    print("[5] Creating S3 buckets ...")
    c = s3()
    for b in BUCKETS:
        try:
            c.create_bucket(Bucket=b["name"])
            if b["policy"]:
                c.put_bucket_policy(Bucket=b["name"], Policy=json.dumps(b["policy"]))
            if b["block"]:
                c.put_public_access_block(
                    Bucket=b["name"], PublicAccessBlockConfiguration=b["block"]
                )
            print(f"    -> Bucket '{b['name']}' created — {b['desc']}")
        except ClientError as e:
            if "BucketAlreadyOwnedByYou" in str(e) or "BucketAlreadyExists" in str(e):
                print(f"    -> Bucket '{b['name']}' already exists")
            else:
                print(f"    -> Bucket '{b['name']}' FAILED: {e}")



SGS = [
    {
        "name": "SSH-Open-World",
        "desc": "SSH open to the entire internet",
        "ingress": [
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
        "egress": [
            {
                "IpProtocol": "-1",
                "FromPort": -1,
                "ToPort": -1,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
    },
    {
        "name": "RDP-Open-World",
        "desc": "RDP open to the entire internet",
        "ingress": [
            {
                "IpProtocol": "tcp",
                "FromPort": 3389,
                "ToPort": 3389,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
        "egress": [
            {
                "IpProtocol": "-1",
                "FromPort": -1,
                "ToPort": -1,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
    },
    {
        "name": "WebSG",
        "desc": "HTTP and HTTPS open to the world",
        "ingress": [
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 443,
                "ToPort": 443,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
        "egress": [
            {
                "IpProtocol": "-1",
                "FromPort": -1,
                "ToPort": -1,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
    },
    {
        "name": "InternalSG",
        "desc": "Internal-only — RFC1918 traffic",
        "ingress": [
            {
                "IpProtocol": "-1",
                "FromPort": -1,
                "ToPort": -1,
                "IpRanges": [
                    {"CidrIp": "10.0.0.0/8"},
                    {"CidrIp": "172.16.0.0/12"},
                    {"CidrIp": "192.168.0.0/16"},
                ],
            },
        ],
        "egress": [
            {
                "IpProtocol": "-1",
                "FromPort": -1,
                "ToPort": -1,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
    },
]


def create_security_groups():
    print("[6] Creating security groups ...")
    c = ec2()
    sg_ids = {"default": None}
    try:
        default_sgs = c.describe_security_groups(
            Filters=[{"Name": "group-name", "Values": ["default"]}]
        )["SecurityGroups"]
        if default_sgs:
            sg_ids["default"] = default_sgs[0]["GroupId"]
    except ClientError:
        pass

    for sg in SGS:
        try:
            resp = c.create_security_group(GroupName=sg["name"], Description=sg["desc"])
            gid = resp["GroupId"]
            sg_ids[sg["name"]] = gid
            c.authorize_security_group_ingress(GroupId=gid, IpPermissions=sg["ingress"])
            c.authorize_security_group_egress(GroupId=gid, IpPermissions=sg["egress"])
            print(f"    -> SG '{sg['name']}' ({gid}) — {sg['desc']}")
        except ClientError as e:
            if "InvalidGroup.Duplicate" in str(e):
                existing = c.describe_security_groups(
                    Filters=[{"Name": "group-name", "Values": [sg["name"]]}]
                )["SecurityGroups"]
                if existing:
                    sg_ids[sg["name"]] = existing[0]["GroupId"]
                print(f"    -> SG '{sg['name']}' already exists")
            else:
                print(f"    -> SG '{sg['name']}' FAILED: {e}")
    return sg_ids




def create_instance_profiles():
    """Create instance profiles so EC2 instances can reference IAM roles."""
    print("[7a] Creating instance profiles ...")
    c = iam()
    profiles = {}
    for role_name in ["EC2-S3-ReadRole"]:
        try:
            c.create_instance_profile(InstanceProfileName=role_name)
            c.add_role_to_instance_profile(
                InstanceProfileName=role_name, RoleName=role_name
            )
            profiles[role_name] = role_name
            print(f"    -> Instance profile '{role_name}' created")
        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                print(f"    -> Instance profile '{role_name}' already exists")
                profiles[role_name] = role_name
            else:
                print(f"    -> Instance profile '{role_name}' FAILED: {e}")
    return profiles


def create_ec2_instances(sg_ids):
    print("[7b] Creating EC2 instances ...")
    c = ec2()
    r = ec2_resource()

    vpc_id = None
    try:
        vpcs = list(r.vpcs.all())
        if vpcs:
            vpc_id = vpcs[0].id
            print(f"    -> Using existing VPC: {vpc_id}")
        else:
            vpc = r.create_vpc(CidrBlock="10.0.0.0/16")
            vpc.wait_until_available()
            vpc_id = vpc.id
            print(f"    -> Created VPC: {vpc_id}")
    except ClientError as e:
        print(f"    -> VPC setup FAILED: {e}")
        return

    subnet_id = None
    try:
        subnets = list(r.subnets.all())
        if subnets:
            subnet_id = subnets[0].id
            print(f"    -> Using existing subnet: {subnet_id}")
        else:
            subnet = r.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24")
            subnet_id = subnet.id
            print(f"    -> Created subnet: {subnet_id}")
    except ClientError as e:
        print(f"    -> Subnet setup FAILED: {e}")
        return

    INSTANCES = [
        {
            "name": "WebServer-01",
            "sg": sg_ids.get("WebSG"),
            "iam_profile": None,
            "desc": "Public web server — HTTP/HTTPS accessible from anywhere",
        },
        {
            "name": "BastionHost",
            "sg": sg_ids.get("SSH-Open-World"),
            "iam_profile": "EC2-S3-ReadRole",
            "desc": "SSH bastion with S3 read role attached",
        },
        {
            "name": "Database-01",
            "sg": sg_ids.get("InternalSG"),
            "iam_profile": None,
            "desc": "Internal database — only reachable from within the VPC",
        },
    ]

    for inst in INSTANCES:
        try:
            sg_ids_list = [inst["sg"]] if inst.get("sg") else []
            launch_kw = dict(
                ImageId="ami-0abcdef1234567890",
                MaxCount=1,
                MinCount=1,
                InstanceType="t2.micro",
                SubnetId=subnet_id,
                SecurityGroupIds=sg_ids_list,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            tag("Name", inst["name"]),
                            tag("Environment", "lab"),
                            tag("Owner", "mooaws"),
                        ],
                    }
                ],
            )
            if inst.get("iam_profile"):
                launch_kw["IamInstanceProfile"] = {"Name": inst["iam_profile"]}
            reservation = c.run_instances(**launch_kw)
            instance_id = reservation["Instances"][0]["InstanceId"]
            print(f"    -> EC2 '{inst['name']}' ({instance_id}) — {inst['desc']}")
        except ClientError as e:
            print(f"    -> EC2 '{inst['name']}' FAILED: {e}")


def main():
    print("=" * 60)
    print("  MooAWS Comprehensive Lab — Setting up resources")
    print("=" * 60)

    caller = sts().get_caller_identity()
    print(f"\n  Floci endpoint : {ENDPOINT_URL}")
    print(f"  Account        : {caller['Account']}\n")
    print("-" * 60)

    custom_arns = create_customer_policies()
    print()
    create_users()
    print()
    create_groups(custom_arns)
    print()
    create_roles()
    print()
    create_buckets()
    print()
    sg_ids = create_security_groups()
    print()
    create_instance_profiles()
    print()
    create_ec2_instances(sg_ids)

    print("\n" + "=" * 60)
    print("  Lab ready! Run MooAWS to enumerate all resources:")
    print(f"\n    python3 main.py --endpoint-url {ENDPOINT_URL} --region {REGION}")
    print("\n  Or use --default if your ~/.aws/credentials is configured:")
    print("    python3 main.py --default --endpoint-url <url>")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
