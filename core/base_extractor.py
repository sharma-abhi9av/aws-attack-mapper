import abc
import botocore.exceptions

class BaseExtractor(abc.ABC):
    SERVICE_NAME =""                       # subclass sets this to "iam", "s3" etc
    def __init__(self,client):             # common in roles.py, users.py, etc
        self.client = client 

    @abc.abstractmethod 
    def extract(self):                     # every child must implement it.
        ...

    def _paginate(self, method, result_key, **kwargs) : # the shared pagination logic
        results =[]
        try:
            paginator = self.client.get_paginator(method)
            for page in paginator.paginate(**kwargs):
                results.extend(page.get(result_key, []))
        except botocore.exceptions.ClientError as e:
            code = e.response["Error"]["Code"]
            print(f"API error during: {method}:{code}")
        return results

    def _safe_call(self, method_name, **kwargs):
        try:
            method = getattr(self.client, method_name)
            return method(**kwargs)
        except botocore.exceptions.ClientError as e:
            Code = e.response["Error"]["Code"]
            print(f"{method_name} failed: {Code}")
            return None
                