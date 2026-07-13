from core.base_extractor import BaseExtractor

class LambdaFunctionsExtractor(BaseExtractor):
    SERVICE_NAME = "lambda"

    def extract(self):
        """
        https://docs.aws.amazon.com/boto3/latest/reference/services/lambda/client/list_functions.html
        https://docs.aws.amazon.com/boto3/latest/reference/services/lambda/client/get_function_url_config.html
        https://docs.aws.amazon.com/boto3/latest/reference/services/lambda/paginator/ListFunctions.html
        """  
        functions = self._paginate("list_functions", "Functions")
        enriched = []
        for function in functions:
            # fetch function URL config, not all functions have one, so _safe_call
            url_config = self._safe_call(
                "get_function_url_config",
                FunctionName=function["FunctionName"]
            )
            enriched.append({
                "FunctionName":   function["FunctionName"],
                "FunctionArn":    function["FunctionArn"],
                "Runtime":        function.get("Runtime"),
                "Role":           function.get("Role"), # Lambda runs as thi role, if attacker can invoke/modify function, they get role's permissions
                "State":          function.get("State"),
                "Description":    function.get("Description"),
                "Environment":    function.get("Environment", {}).get("Variables", {}), # may contain secrets
                "VpcId":          function.get("VpcConfig", {}).get("VpcId"),
                "SecurityGroups": function.get("VpcConfig", {}).get("SecurityGroupIds", []),
                "FunctionUrl":    url_config.get("FunctionUrl") if url_config else None,
                "UrlAuthType":    url_config.get("AuthType") if url_config else None,
            })
        return enriched