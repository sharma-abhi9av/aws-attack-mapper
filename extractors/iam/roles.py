from core.base_extractor import BaseExtractor

class RolesExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        """ 
        Attached policies: list_attached_role_policies, key AttachedPolicies, kwarg RoleName=rolename
        Inline names: list_role_policies, key PolicyNames, kwarg RoleName=rolename
        Each inline doc: get_role_policy with RoleName=rolename, PolicyName=name, document at resp["PolicyDocument"]
        """
        roles= self._paginate("list_roles", "Roles")
        enriched = []
        
        for role in roles:
            rolename = role["RoleName"]
            
            role["AttachedPolicies"] = self._paginate("list_attached_role_policies", "AttachedPolicies", RoleName=rolename)         
            
            policy_names = self._paginate("list_role_policies", "PolicyNames", RoleName=rolename)
            role["InlinePolicies"] = []
            
            for policy_name in policy_names:
                resp= self._safe_call("get_role_policy", RoleName=rolename, PolicyName=policy_name)
                if resp:
                    role["InlinePolicies"].append({
                        "PolicyName": policy_name,
                        "Document": resp["PolicyDocument"]
                    })
            enriched.append(role)
        return enriched