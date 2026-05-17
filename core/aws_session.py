import sys
import botocore.exceptions
import boto3

class AWSSession:
    def __init__(self,profile_name = None, region_name = None, endpoint_url = None):
        self._endpoint_url = endpoint_url
        try:
            self._session = boto3.Session(
                profile_name =profile_name,
                region_name=region_name,
            )
        except botocore.exceptions.ProfileNotFound as e:
            print(f"AWS profile not found: {e}")
            sys.exit(1)
    def get_client(self,service):
        kwargs ={}
        if self._endpoint_url:
            kwargs["endpoint_url"] = self._endpoint_url
        return self._session.client(service, **kwargs)