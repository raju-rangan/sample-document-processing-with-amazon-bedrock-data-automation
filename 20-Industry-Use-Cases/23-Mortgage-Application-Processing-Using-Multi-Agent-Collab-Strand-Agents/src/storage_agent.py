from strands import Agent
from strands.tools.mcp import MCPClient
import boto3
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters
import os
from mcp.client.streamable_http import streamablehttp_client 
import sys
import utils


STORAGE_AGENT_SYSTEM_PROMPT = """
<context>
You are a data storage expert for mortgage application automation. 
- DynamoDB table: mortgage-applications
</context>

<instructions>
1. Receive mortgage request results from a Bedrock data pipeline.
2. Parse and classify all incoming data into:
   - Structured data: fields matching the defined DynamoDB schema.
   - Unstructured data: document scans, images, PDFs, long text fields, or notes.
3. Store structured data to the DynamoDB table "mortgage-applications" with the following schema:
</instructions>
"""

CLIENT_ID = "35j0m1mieai58f3k6heknnvltb"
CLIENT_SECRET = "idjpa3ep9pve1fsfg03i3lei8njtd6j2k0e78rg6suje5qf6bqp"
TOKEN_URL = "https://us-east-1bhassuci6.auth.us-east-1.amazoncognito.com/oauth2/token"

REGION = os.environ.get('AWS_REGION','us-east-1')
RESOURCE_SERVER_ID = "sample-agentcore-gateway-id"
RESOURCE_SERVER_NAME = "sample-agentcore-gateway-name"
scopeString = f"{RESOURCE_SERVER_ID}/gateway:read {RESOURCE_SERVER_ID}/gateway:write"
user_pool_id = 'us-east-1_bHASSuci6'

print("Requesting the access token from Amazon Cognito authorizer...May fail for some time till the domain name propogation completes")
token_response = utils.get_token(user_pool_id, CLIENT_ID, CLIENT_SECRET, scopeString, REGION)
token = token_response["access_token"]
print("Token response:", token)

session = boto3.Session(
    region_name=REGION,
)

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    boto_session=session,
)

env = os.environ.copy()
env["UV_CONSTRAINT"] = "requirements.txt"

aws_api_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-api-mcp-server@latest"],
        env=env
    )
))

gateway_url = "https://testgwforlambda-oivlepaosr.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

def create_streamable_http_transport():
    return streamablehttp_client(gateway_url,headers={"Authorization": f"Bearer {token}"})


mcp_client = MCPClient(create_streamable_http_transport)

# mcp_client.start()
# aws_api_mcp_client.start()

# tools = mcp_client.list_tools_sync() + aws_api_mcp_client.list_tools_sync()

# storage_agent = Agent(
#     name="storage_agent",
#     system_prompt=STORAGE_AGENT_SYSTEM_PROMPT,
#     model=bedrock_model,
#     tools=tools,
# )
