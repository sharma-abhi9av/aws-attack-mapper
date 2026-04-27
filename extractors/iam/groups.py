from core.base_extractor import BaseExtractor

class GroupsExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        return self._paginate("list_groups", "Groups")