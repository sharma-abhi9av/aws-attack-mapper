import os

class Neo4jConfig:
    URI      = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    USER     = os.environ.get("NEO4J_USER",     "neo4j")
    PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4j")

class AWSConfig:
    DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")