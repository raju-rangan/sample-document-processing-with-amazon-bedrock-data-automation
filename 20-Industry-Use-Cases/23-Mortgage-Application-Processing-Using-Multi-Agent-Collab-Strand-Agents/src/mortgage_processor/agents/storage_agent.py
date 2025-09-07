from strands.tools.mcp import MCPClient
import boto3
from strands.models import BedrockModel
import os

STORAGE_AGENT_SYSTEM_PROMPT = """
You are a data storage expert for mortgage applications 

IMPORTANT: If successful ONLY return 'success' otherwise, return 'failure' and 'error' containing the error message
"""

REGION = os.environ.get('AWS_REGION','us-east-1')

session = boto3.Session(
    region_name=REGION,
)

bedrock_model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    temperature=0.0,
    boto_session=session,
)