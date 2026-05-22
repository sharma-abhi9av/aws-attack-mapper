from core.base_extractor import BaseExtractor
class PoliciesExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        """
        Extracts Customer-managed IAM Policies and fetches their permission documents.

        Why Scope="Local" ?
        To understand that you need to understand  AWS has two types of managed policies:
        - list_policies returns all policies in the account, including AWS-managed and customer-managed policies.
        - Scope="AWS" include the policies created by AWS.
        - We fetch local to cut the noise of thousands of AWS-managed policies, however we will pull Attached AWS policies separately so we do not miss attack paths like 'AdministratorAccess'.
        
        Why are we fetching document separately?
        - the answer comes from the output of list_policies, actually list_policies does not return the policy document like what is ALLOWED or DENIED,
          it only returns metadata about the policy.
        """
        policies= self._paginate("list_policies", "Policies", Scope="Local")
        aws_policies = self._paginate("list_policies", "Policies",Scope="AWS",OnlyAttached=True)
        # OnlyAttached=True avoids pulling thousands of unused AWS built-ins
        # We need these because AdministratorAccess etc are common attack path components
        enriched = []
        for policy in policies:
            policyarn = policy["Arn"]
            
            resp = self._safe_call("get_policy_version", PolicyArn=policyarn, VersionId=policy["DefaultVersionId"])
            # Policies can have multiple versions as they get updated, DefaultVersionId is the currently active version
            if resp:
                policy["Document"] = resp["PolicyVersion"]["Document"]
            else:
                policy["Document"] = None
            enriched.append(policy)

        for policy in aws_policies:
            policyarn = policy["Arn"]
            resp = self._safe_call(
                "get_policy_version",
                PolicyArn=policyarn,
                VersionId=policy["DefaultVersionId"]
            )
            if resp:
                policy["Document"] = resp["PolicyVersion"]["Document"]
            else:
                policy["Document"] = None
            enriched.append(policy)
        return enriched