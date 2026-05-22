from core.base_extractor import BaseExtractor

class RolesExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        """ 
        Extracts all IAM Roles from AWS and enriches each role with:
        - Managed policies attached to them
        - Inline policies
        """
        roles= self._paginate("list_roles", "Roles")
        enriched = []
        
        for role in roles:
            rolename = role["RoleName"]
            # AssumeRolePolicyDocument is already in the role object from list_roles
            # it shows who can assume this role, making it critical for mapping attack paths
            # However, we don't need to fetch it separately, it comes free with list_roles
            
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