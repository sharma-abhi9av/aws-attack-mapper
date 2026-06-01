import json
from core.base_extractor import BaseExtractor

class S3BucketsExtractor(BaseExtractor):
    SERVICE_NAME = "s3"

    def extract(self):
        resp = self._safe_call("list_buckets")    # Return a dict with list of all bucket in the account,
        buckets = resp["Buckets"] if resp else [] # List of dicts.
        for bucket in buckets:
            name = bucket["Name"]

            # Bucket Policy
            policy_resp = self._safe_call("get_bucket_policy", Bucket=name) # fetches who has permission to access the bucket 
            if policy_resp:
                bucket["Policy"] = json.loads(policy_resp["Policy"]) # AWS returns the policy as a string so we convert it into a dict for easier use later on.
            else:
                bucket["Policy"] = None

            block_resp = self._safe_call("get_public_access_block", Bucket=name)
            if block_resp:
                bucket["PublicAccessBlock"] = block_resp["PublicAccessBlockConfiguration"]
            else:
                bucket["PublicAccessBlock"] = None

            # Bucket Location (Region)
            location_resp = self._safe_call("get_bucket_location", Bucket=name)
            if location_resp:
                bucket["Region"] = location_resp["LocationConstraint"]
            else:
                bucket["Region"] = None
        return buckets