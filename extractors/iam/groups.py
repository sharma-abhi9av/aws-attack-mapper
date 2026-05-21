from tokenize import group

from core.base_extractor import BaseExtractor

class GroupsExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        groups= self._paginate("list_groups", "Groups")
        enriched = []
        
        for group in groups:
            groupname = group["GroupName"]
            members = self._safe_call("get_group", GroupName=groupname)
            group["Members"] = members["Users"] if members else []

            # Attached policies: list_attached_group_policies, key AttachedPolicies, kwarg GroupName=groupname
            group["AttachedPolicies"] = self._paginate("list_attached_group_policies", "AttachedPolicies", GroupName=groupname)         
            
            # Inline names: list_group_policies, key PolicyNames, kwarg GroupName=groupname
            policy_names = self._paginate("list_group_policies", "PolicyNames", GroupName=groupname)
            group["InlinePolicies"] = []
            
            for policy_name in policy_names:
                resp= self._safe_call("get_group_policy", GroupName=groupname, PolicyName=policy_name)
                if resp:
                    group["InlinePolicies"].append({
                        "PolicyName": policy_name,
                        "Document": resp["PolicyDocument"]
                    })
            enriched.append(group)
        return enriched