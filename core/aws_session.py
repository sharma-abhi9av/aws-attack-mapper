import sys                  # Module for stopping the code if certain conditions met.
import botocore.exceptions  # Module for handling some errors in AWSSession.
import boto3                # The official SDK for AWS.
class AWSSession:
    """
    In class AWSSession, we make two functions.
    """
    def __init__(self,profile_name = None, region_name = None, endpoint_url = None):
        """
        The initializer, which initialise the AWS session, with parameter profile_name, region_name and endpoint_url,
        If user doesn't provide any of these, the default value goes as None instead of raising an error.

        Then we use boto3 to validate the session, if no profile is found the botocore.exceptions raise an ProfileNotFound error,
        then sys module does the work of quitely stopping the script from running further.
        """
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
        """
        The get_client function, which works as getting the client for different service like IAM,S3,EC2, etc.,
        It takes service name as input, and an optional endpoint_url,
        if there is no endpoint_url provided **kwargs does the work to safely ignore it, and work further 
        """
        kwargs ={}
        if self._endpoint_url:
            kwargs["endpoint_url"] = self._endpoint_url
        return self._session.client(service, **kwargs)