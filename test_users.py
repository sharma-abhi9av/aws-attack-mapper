from extractors.iam.users import UsersExtractor
class FakePage:
        def get(self, key, default):
            if key == "Users":
                return [
                    {"UserName": "alice", "UserId": "111", "Arn": "arn:aws:iam::123:user/alice"},
                    {"UserName": "bob",   "UserId": "222", "Arn": "arn:aws:iam::123:user/bob"},
                ]
            return default
    class FakePaginator:
        def paginate(self):
            return [FakePage(), FakePage()]   pretend 2 pages
    class FakeIAMClient:
        def get_paginator(self, method_name):
            print(f"get_paginator called with: {method_name}")
            return FakePaginator()
     Now test it
    fake_client = FakeIAMClient()
    extractor = UsersExtractor(fake_client)
    result = extractor.extract()
    print(f"Total users found: {len(result)}")
    for user in result:
        print(f"  - {user['UserName']}")