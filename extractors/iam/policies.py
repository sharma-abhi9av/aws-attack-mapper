from core.base_extractor import BaseExtractor
class PoliciesExtractor(BaseExtractor):
    SERVICE_NAME="iam"
    def extract(self):
        return self._paginate("list_policies", "Policies", Scope="Local")