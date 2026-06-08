import os 
import argparse     # Module for passing arguments such as, python3 main.py --help
# Importing out modules 
from core.aws_session            import AWSSession
from extractors.iam.users        import UsersExtractor
from extractors.iam.roles        import RolesExtractor
from extractors.iam.groups       import GroupsExtractor
from extractors.iam.policies     import PoliciesExtractor
from extractors.s3.buckets       import S3BucketsExtractor
from extractors.ec2.instances    import EC2Extractor
from exporters.json_writer       import export_to_json
from parsers.normalizer          import normalize_users, normalize_roles, normalize_groups, normalize_policies, normalize_buckets, normalize_ec2

def run_extraction(session, out_dir):
    """
    We create an iam_client, which is shared by all IAM extractors, similiary we can create client for every service our tools handles
    For example: 
        s3_client  = session.get_client("s3")
        sts_client = session.get_client("sts")
    """
    iam_client = session.get_client("iam") 
    s3_client = session.get_client("s3")
    ec2_client = session.get_client("ec2")

    """
    Extraction plan is list of ready to use, extractor object and filename pair.
    Adding new extractor later. we write just one line here.
    """
    extraction_plan = [
    (UsersExtractor(iam_client),    "users.json",       normalize_users),
    (RolesExtractor(iam_client),    "roles.json",       normalize_roles),
    (PoliciesExtractor(iam_client), "policies.json",    normalize_policies),
    (GroupsExtractor(iam_client),   "groups.json",      normalize_groups),
    (S3BucketsExtractor(s3_client), "s3_buckets.json",  normalize_buckets),
    (EC2Extractor(ec2_client), "ec2_instances.json", normalize_ec2),
    ]

    """
    Every extractor use 'extract()' ao we can make a single loop for every extractor
    Inside loop we call extract(), which goes to UsersExtractor, RolesExtractor, etc.
    Save the files in /output directory by default.  
    """

    for extractor, filename, normalizer in extraction_plan:
        print(f"Running {extractor.__class__.__name__}...")
        data = extractor.extract()
        normalised = normalizer(data)
        filepath = os.path.join(out_dir, filename)
        export_to_json(normalised, filepath)

def main():
    """
    We use argparse to read what user type in terminal.
    For example - python3 main.py --profile localstack --endpoint-url http://localhost:4566
    """
    parser = argparse.ArgumentParser(description="AWS Attack Mapper")
    parser.add_argument("--profile",        default = None,         help ="AWS CLI Profile")
    parser.add_argument("--region",         default = "us-east-1",  help ="Region for AWS")
    parser.add_argument("--endpoint-url",   default=None,           help="Url endpoint")
    parser.add_argument("--out-dir",        default="output",       help="Output folder for Json files")
    args = parser.parse_args()
    
    """
    Create the output folder if doesn't exists, exist_ok makes sure it doesn't crash if folder already exists.
    Then creates a session with args user provided, If they do not provide something boto3 uses defaults.
    """
    os.makedirs(args.out_dir, exist_ok=True)
    session = AWSSession(
        profile_name=args.profile,
        region_name=args.region,
        endpoint_url=args.endpoint_url,
    )
    session.get_caller_identity()
    # Run extraction
    run_extraction(session, args.out_dir)
    print("\nExtraction Complete")

# Run main only if  main.py is executed directly
if __name__ == "__main__":
    main()