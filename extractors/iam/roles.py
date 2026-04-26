class RolesExtractor:
    def __init__(self, client):
        self.client = client
    def extract(self):
        all_roles = []
        paginator = self.client.get_paginator("list_roles")
        for page in paginator.paginate():
            roles = page.get("Roles",[])
            all_roles.extend(roles)
        return all_roles
