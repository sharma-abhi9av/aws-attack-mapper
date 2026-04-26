import abc
import botocore.exceptions

class BaseExtractor(abc.ABC):
    SERVICE_NAME =""                       # subclass sets this to "iam", "s3" etc
    def __init__(self,client):             # common in roles.py, users.py, etc
        self.client = client 

    @abc.abstractmethod 
    def extract(self):                     # every child must implement it.
        ...