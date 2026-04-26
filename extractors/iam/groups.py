class GroupsExtractor:
    def __init__(self, client):
        self.client = client 
    def extract(self):
        all_groups =[]
        paginator= self.client.get_paginator("list_groups")
        for page in paginator.paginate():
            groups= page.get("Groups",[])
            all_groups.extend(groups)
        return all_groups