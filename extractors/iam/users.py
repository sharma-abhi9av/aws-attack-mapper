class UsersExtractor:
    def __init__(self, client):
        self.client = client 
    # Store the client so every method can use it.
    def extract(self):
    # Get the users from aws and return them in flat list.
        all_users = [] # Empty list for extending users later.
        paginator = self.client.get_paginator("list_users") # getting whole paiganator through get_paginator method
        for page in paginator.paginate():            # looping through the paginator, page by page
            users = page.get("Users", []) # if not users, return []                
            all_users.extend(users)           # extent the users in all_users
        return all_users

