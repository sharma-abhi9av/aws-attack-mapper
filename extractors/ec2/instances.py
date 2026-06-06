from core.base_extractor import BaseExtractor

class EC2Extractor(BaseExtractor):
    SERVICE_NAME = "ec2"

    def extract(self):
        """
        You can refer to https://docs.aws.amazon.com/boto3/latest/reference/services/ec2/client/describe_instances.html to see sample output and keys.
        """
        reservations = self._paginate("describe_instances", "Reservations") # get all reservations
        instances = []
        # AWS returns nested results so flattening to get actual instances.
        for reservation in reservations:
            for instance in reservation["Instances"]:
                instances.append(instance)
        
        enriched = []
        for instance in instances:
            instance_id = instance["InstanceId"]
            # Appending results we care about 
            enriched.append({
            "InstanceId":        instance["InstanceId"],
            "State":             instance["State"]["Name"],
            "PublicIpAddress":   instance.get("PublicIpAddress", None),
            "PrivateIpAddress":  instance.get("PrivateIpAddress", None),
            "InstanceType":      instance.get("InstanceType", None),
            "KeyName":           instance.get("KeyName", None),
            "IamInstanceProfile": instance.get("IamInstanceProfile", None),
            "SecurityGroups":    instance.get("SecurityGroups", []),
            })
        return enriched