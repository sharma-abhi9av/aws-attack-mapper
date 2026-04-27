from core.base_extractor import BaseExtractor

class RolesExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        return self._paginate("list_roles", "Roles")