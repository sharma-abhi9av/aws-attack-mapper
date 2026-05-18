import os # Import os module to fetch the environment variables 

class Neo4jConfig:
    """
    For neo4j config, the code looks in environment variables for the URI, Username and Password are present,
    if not it goes with the default values hardcoded here. 
    """
    URI      = os.environ.get("NEO4J_URI", "bolt://localhost:7687") 
    USER     = os.environ.get("NEO4J_USER",     "neo4j")
    PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4j")

class AWSConfig:
    """
    For AWSconfig, region_name it looks for region if any specified in local environment, else it goes with 'us-east-1' 
    """
    DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")