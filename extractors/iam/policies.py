from core.base_extractor import BaseExtractor
class PoliciesExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        policies= self._paginate("list_policies", "Policies", Scope="Local")
        enriched = []
        for policy in policies:
            policyname = policy["PolicyName"]
            policyarn = policy["Arn"]
            # Get default version document: get_policy_version with PolicyArn=policyarn, VersionId=policy["DefaultVersionId"], document at resp["PolicyVersion"]["Document"]
            resp = self._safe_call("get_policy_version", PolicyArn=policyarn, VersionId=policy["DefaultVersionId"])
            if resp:
                policy["Document"] = resp["PolicyVersion"]["Document"]
            else:
                policy["Document"] = None
            enriched.append(policy)
        return enriched