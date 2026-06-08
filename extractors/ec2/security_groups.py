from core.base_extractor import BaseExtractor

class SecurityGroupExtractor(BaseExtractor):
    SERVICE_NAME = "ec2"

    def extract(self):
        security_groups = self._paginate("describe_security_groups", "SecurityGroups")
        enriched = []
        for sg in security_groups:
            enriched.append({
                "GroupId":         sg["GroupId"],
                "GroupName":       sg["GroupName"],
                "Description":     sg.get("Description", ""),
                "VpcId":           sg.get("VpcId", None),
                "InboundRules":    sg.get("IpPermissions", []),
                "OutboundRules":   sg.get("IpPermissionsEgress", []),
                "Tags":            sg.get("Tags", []),
                "HasPublicInbound": any(self._is_dangerous(r) for r in sg.get("IpPermissions", []))  # to check if target is exposed
            })
        return enriched

    def _is_dangerous(self, rule):
        # check if rule allows traffic from anywhere on the internet
        for ip_range in rule.get("IpRanges", []):
            if ip_range.get("CidrIp") == "0.0.0.0/0":
                return True
        return False