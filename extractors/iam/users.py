from core.base_extractor import BaseExtractor

class UsersExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        """
        Extracts all IAM Users from AWS and enriches each user with:
        - Groups they belong to
        - Managed policies attached to them
        - Inline policies 

        Why ?
        list_users alone gives identity info only (name, ARN, ID).
        Without groups and policies, we cannot see what a user can do or what attack paths they might enable. 
        Adding additional data through enrichment is what makes the data useful for building an attack graph.
        """
        
        users = self._paginate("list_users", "Users")
        enriched = []
        # We can't modify 'users' while building on it, enriched collects each fully-built user dict and
        # by the end it contains everything users had + Groups, AttachedPolicies, InlinePolicies.
        
        for user in users:
            username = user["UserName"]
            user["Groups"] = self._paginate("list_groups_for_user", "Groups", UserName=username)          
            user["AttachedPolicies"] = self._paginate("list_attached_user_policies", "AttachedPolicies", UserName=username)
            policy_names = self._paginate("list_user_policies", "PolicyNames", UserName=username)

            user["InlinePolicies"] = []            
            # Inline policies require two steps:
            # 1. get the list of names (done above with list_user_policies)
            # 2. fetch each policy document individually by name
            # So, we start with empty list and append each one as we fetch it
            
            for policy_name in policy_names:
                resp= self._safe_call("get_user_policy", UserName=username, PolicyName=policy_name)
                if resp:
                    user["InlinePolicies"].append({
                        "PolicyName": policy_name,
                        "Document": resp["PolicyDocument"]
                    })
            enriched.append(user)
        return enriched
    