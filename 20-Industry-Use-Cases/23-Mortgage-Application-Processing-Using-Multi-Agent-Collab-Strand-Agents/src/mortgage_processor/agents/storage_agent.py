from strands.tools.mcp import MCPClient
import boto3
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters
import os

STORAGE_AGENT_SYSTEM_PROMPT = """
You are a data storage expert for mortgage applications. 

Always output valid JSON objects for all nested fields.

IMPORTANT: If successful ONLY return 'success' otherwise, return 'failure' and 'error' containing the error message
"""

REGION = os.environ.get('AWS_REGION','us-east-1')

session = boto3.Session(
    region_name=REGION,
)

bedrock_model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    temperature=0.7,
    boto_session=session,
)

env = os.environ.copy()

aws_api_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-api-mcp-server@latest"],
        env=env
    )
))