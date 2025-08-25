from strands.tools.mcp import MCPClient
import boto3
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters
import os

STORAGE_AGENT_SYSTEM_PROMPT = """
You are a NoSQL data storage expert for mortgage applications. 
You are storing applications to the DynamoDB table: mortgage-applications

IMPORTANT: If successful ONLY return 'success' otherwise, return 'failure' and 'error' containing the error message

Required Fields:
- `borrower_name` (String)
- `status` (String)
- `application_date` (String)
- `loan_originator_id` (String)
- `property_state` (String)
- `loan_amount` (Number)
- `ssn` (String)

Storage Format:
- Store all complex nested data (personal_information, assets, liabilities, employment_information, etc.) in `configuration` field as JSON
- Add metadata: `created_at`, `updated_at` (ISO timestamps), `version` ("1.0")
- Include `name` and `description` fields for application summary
"""

REGION = os.environ.get('AWS_REGION','us-east-1')

session = boto3.Session(
    region_name=REGION,
)

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
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