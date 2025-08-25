from strands.tools.mcp import MCPClient
import boto3
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters
import os

DATA_EXTRACTION_SYSTEM_PROMPT = """
<context>
You are a specialized data extraction agent. You analyze mortgage documents and extract data.
</context>

<instructions>
1. Using bedrock data automation IRLA project, Extract all relevant data from mortgage applications, loan documents, financial statements, and supporting materials
2. Send the analysis result as a response
</instructions>
"""

session = boto3.Session(
    region_name=os.environ.get('AWS_REGION','us-east-1'),
)

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    boto_session=session,
)

env = os.environ.copy()

bda_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-bedrock-data-automation-mcp-server@latest"],
        env=env
    )
))