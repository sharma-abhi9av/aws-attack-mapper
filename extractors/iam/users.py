from core.base_extractor import BaseExtractor

class UsersExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        return self._paginate("list_users", "Users")