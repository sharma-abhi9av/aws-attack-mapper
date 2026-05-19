import boto3
from core.base_extractor import BaseExtractor

class UsersExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        users = self._paginate("list_users", "Users")
        enriched = []
        for user in users:
            username = user["UserName"]
            # Groups --> list_groups_for_user, key = Groups 
            user["Groups"] = self._paginate("list_groups_for_user", "Groups", UserName=username)
            # Attached policies --> list_attached_user_policies, key = AttachedPolicies
            user["AttachedPolicies"] = self._paginate("list_attached_user_policies", "AttachedPolicies", UserName=username)
            # Inline policy names  --> list_user_policies, key = PolicyNames 
            policy_names = self._paginate("list_user_policies", "PolicyNames", UserName=username)
            user["InlinePolicies"] = []
            for policy_name in policy_names:
                resp= self._safe_call("get_user_policy", UserName=username, PolicyName=policy_name)
                if resp:
                    user["InlinePolicies"].append({
                        "PolicyName": policy_name,
                        "Document": resp["PolicyDocument"]
                    })
            enriched.append(user)
        return enriched
    