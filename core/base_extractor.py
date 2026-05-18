import abc                      # Module for setting up abstract method so every child implement.
import botocore.exceptions      # Module for AWS API errors

class BaseExtractor(abc.ABC):
    """
    Class BaseExtractor, it have an variable specified as SERVICE_NAME, which is an empty string, and get its value by the subclass.
    For instance, IAM subclass would give SERVICE_NAME the value of 'IAM'. 
    """
    SERVICE_NAME =""                       
    def __init__(self,client):     
        """
        Making client is common in every child so this function helps child class remain simple,
        Example about how an child class uses it.

        class S3Extractor(BaseExtractor):
            SERVICE_NAME = "s3"

            def extract(self):
            # This works because the parent __init__ already saved self.client
            return self._paginate("list_buckets", "Buckets")
        """
        self.client = client 

    @abc.abstractmethod 
    def extract(self):                     
        """
        This function is for making sure every child must implement the extract function, else it won't let it create the object.
        """
        ...

    def _paginate(self, method, result_key, **kwargs) : 
        """
        Why pagination, this comes from the way how AWS return data, a single ListUsers call to AWS IAM returns a default maximum of 100 users.
        So, even if you have thousands of users, the response truncates at 100 (or 1000 objects for s3) and provides a pagination token.
        Child classes share pagination logic so making it here reduce clutter and keep us in track of DRY. 
        For reference visit - https://docs.aws.amazon.com/boto3/latest/guide/paginators.html
        The function paginate work as follows :
        - We create an empty list.
        - We setup an try/except block.
        - Inside try, we setup an variable paginator, which works by asking client to gets the pages by method(for example 'list_users') specified in the boto3 library.
        - When paginator fetch the information we run an loop which goes page by page, taking the extra argument if any, and then return results.
        - For those not familiar, using extend over append here is used to get flat list, instead of list in list.
        - If the AWS call fails, it raise an ClientError, with the name of method, and the code.
         
        """
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
        """
        Why safe_call, Imagine you want to look up details for a specific IAM user named "john-doe".
        To do this, you pass these arguments into _safe_call, for instance method_name as get_user and **kwargs as additional arg - UserName="john-doe" 
        If you call an AWS command directly and it fails, your entire script crashes instantly.
        Child classes share this logic to run single AWS commands without worrying about crashes.

        The function safe_call work as follows:
        - We setup an try/except block.
        - Under try we define an variable method using getattr, to turn a string text into an AWS function
        - Using **kwargs for any dynamic argument (like UserName="john-doe")
        - If it succeeds, it return the response else raise an Error and return None instead of crashing. 
        """
        try:
        
            method = getattr(self.client, method_name)
            return method(**kwargs)
        except botocore.exceptions.ClientError as e:
            Code = e.response["Error"]["Code"]
            print(f"{method_name} failed: {Code}")
            return None
                