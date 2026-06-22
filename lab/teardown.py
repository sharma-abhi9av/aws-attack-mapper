"""
Teardown — removes all resources created by setup.py in reverse dependency order.
"""

import os
import boto3
from botocore.exceptions import ClientError

ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "http://localhost.floci.io:4566")
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
KW = dict(endpoint_url=ENDPOINT_URL, region_name=REGION,
          aws_access_key_id="test", aws_secret_access_key="test")
AWS_PREFIX = "arn:aws:iam::aws:policy"


def iam():
    return boto3.client("iam", **KW)


def s3():
    return boto3.client("s3", **KW)


def ec2():
    return boto3.client("ec2", **KW)


def ec2_resource():
    return boto3.resource("ec2", **KW)


def nuke_ec2_instances():
    print("[1] Terminating EC2 instances ...")
    c = ec2()
    r = ec2_resource()
    try:
        instances = c.describe_instances(Filters=[{"Name": "tag:Owner", "Values": ["mooaws"]}])
        ids = []
        for res in instances.get("Reservations", []):
            for inst in res.get("Instances", []):
                ids.append(inst["InstanceId"])
        if ids:
            c.terminate_instances(InstanceIds=ids)
            print(f"    -> Terminated: {ids}")
        else:
            print("    -> No lab instances found")
    except ClientError as e:
        print(f"    -> Skipping instances: {e}")


def nuke_security_groups():
    print("[2] Deleting security groups ...")
    c = ec2()
    for name in ["SSH-Open-World", "RDP-Open-World", "WebSG", "InternalSG"]:
        try:
            sgs = c.describe_security_groups(Filters=[{"Name": "group-name", "Values": [name]}])["SecurityGroups"]
            for sg in sgs:
                try:
                    c.delete_security_group(GroupId=sg["GroupId"])
                    print(f"    -> Deleted SG '{name}' ({sg['GroupId']})")
                except ClientError as e:
                    print(f"    -> Could not delete SG '{name}': {e}")
        except ClientError:
            print(f"    -> SG '{name}' not found")


def nuke_buckets():
    print("[3] Deleting S3 buckets ...")
    c = s3()
    for bucket in ["public-read-lab", "public-write-lab", "confidential-data", "logs-bucket", "audit-reports"]:
        try:
            # Remove bucket policy first
            try:
                c.delete_bucket_policy(Bucket=bucket)
            except ClientError:
                pass
            # Delete all objects
            objects = c.list_objects_v2(Bucket=bucket).get("Contents", [])
            for obj in objects:
                c.delete_object(Bucket=bucket, Key=obj["Key"])
            c.delete_bucket(Bucket=bucket)
            print(f"    -> Deleted bucket '{bucket}'")
        except ClientError as e:
            print(f"    -> Skipping bucket '{bucket}': {e}")


def nuke_roles():
    print("[4] Deleting IAM roles ...")
    c = iam()
    for role in ["LeakyRole", "EC2-S3-ReadRole", "Lambda-AdminRole"]:
        try:
            # Detach managed policies
            policies = c.list_attached_role_policies(RoleName=role).get("AttachedPolicies", [])
            for p in policies:
                c.detach_role_policy(RoleName=role, PolicyArn=p["PolicyArn"])
            # Delete inline policies
            inline = c.list_role_policies(RoleName=role).get("PolicyNames", [])
            for p in inline:
                c.delete_role_policy(RoleName=role, PolicyName=p)
            # Remove instance profiles (if any)
            profiles = c.list_instance_profiles_for_role(RoleName=role).get("InstanceProfiles", [])
            for ip_ in profiles:
                c.remove_role_from_instance_profile(InstanceProfileName=ip_["InstanceProfileName"], RoleName=role)
            c.delete_role(RoleName=role)
            print(f"    -> Deleted role '{role}'")
        except ClientError as e:
            print(f"    -> Skipping role '{role}': {e}")


def nuke_groups():
    print("[5] Deleting IAM groups ...")
    c = iam()
    for group in ["DeveloperGroup", "S3Team", "AuditTeam"]:
        try:
            # Remove users
            users = c.get_group(GroupName=group).get("Users", [])
            for u in users:
                c.remove_user_from_group(GroupName=group, UserName=u["UserName"])
            # Detach policies
            policies = c.list_attached_group_policies(GroupName=group).get("AttachedPolicies", [])
            for p in policies:
                c.detach_group_policy(GroupName=group, PolicyArn=p["PolicyArn"])
            # Delete inline policies
            inline = c.list_group_policies(GroupName=group).get("PolicyNames", [])
            for p in inline:
                c.delete_group_policy(GroupName=group, PolicyName=p)
            c.delete_group(GroupName=group)
            print(f"    -> Deleted group '{group}'")
        except ClientError as e:
            print(f"    -> Skipping group '{group}': {e}")


def nuke_users():
    print("[6] Deleting IAM users ...")
    c = iam()
    for user in ["Bob-admin", "Alice-dev", "Dave-s3", "Eve-audit"]:
        try:
            # Detach managed policies
            policies = c.list_attached_user_policies(UserName=user).get("AttachedPolicies", [])
            for p in policies:
                c.detach_user_policy(UserName=user, PolicyArn=p["PolicyArn"])
            # Delete inline policies
            inline = c.list_user_policies(UserName=user).get("PolicyNames", [])
            for p in inline:
                c.delete_user_policy(UserName=user, PolicyName=p)
            # Delete access keys
            keys = c.list_access_keys(UserName=user).get("AccessKeyMetadata", [])
            for k in keys:
                c.delete_access_key(UserName=user, AccessKeyId=k["AccessKeyId"])
            # Remove from groups
            groups = c.list_groups_for_user(UserName=user).get("Groups", [])
            for g in groups:
                c.remove_user_from_group(GroupName=g["GroupName"], UserName=user)
            c.delete_user(UserName=user)
            print(f"    -> Deleted user '{user}'")
        except ClientError as e:
            print(f"    -> Skipping user '{user}': {e}")


def nuke_custom_policies():
    print("[7] Deleting custom IAM policies ...")
    c = iam()
    for name in ["DeveloperPolicy", "S3FullAccessPolicy", "AuditReportPolicy"]:
        try:
            policies = c.list_policies(Scope="Local", MaxItems=1000)
            for p in policies["Policies"]:
                if p["PolicyName"] == name:
                    versions = c.list_policy_versions(PolicyArn=p["Arn"])["Versions"]
                    for v in versions:
                        if not v["IsDefaultVersion"]:
                            c.delete_policy_version(PolicyArn=p["Arn"], VersionId=v["VersionId"])
                    c.delete_policy(PolicyArn=p["Arn"])
                    print(f"    -> Deleted policy '{name}'")
                    break
        except ClientError as e:
            print(f"    -> Skipping policy '{name}': {e}")


def nuke_instance_profiles():
    print("[8] Deleting instance profiles ...")
    c = iam()
    for name in ["EC2-S3-ReadRole"]:
        try:
            c.remove_role_from_instance_profile(InstanceProfileName=name, RoleName=name)
            c.delete_instance_profile(InstanceProfileName=name)
            print(f"    -> Deleted instance profile '{name}'")
        except ClientError as e:
            print(f"    -> Skipping instance profile '{name}': {e}")


def nuke_vpc():
    print("[9] Cleaning up VPC ...")
    r = ec2_resource()
    try:
        for vpc in r.vpcs.all():
            if vpc.cidr_block == "10.0.0.0/16":
                # Delete subnets
                for subnet in vpc.subnets.all():
                    subnet.delete()
                vpc.delete()
                print(f"    -> Deleted VPC {vpc.id}")
                break
    except ClientError as e:
        print(f"    -> Skipping VPC: {e}")


def main():
    print("=" * 50)
    print("  MooAWS Lab — Full Teardown")
    print("=" * 50)
    nuke_ec2_instances()
    print()
    nuke_security_groups()
    print()
    nuke_buckets()
    print()
    nuke_roles()
    print()
    nuke_groups()
    print()
    nuke_users()
    print()
    nuke_custom_policies()
    print()
    nuke_instance_profiles()
    print()
    nuke_vpc()
    print("\nTeardown complete.")


if __name__ == "__main__":
    main()
