from typing import Optional
import os
from mcp.client.streamable_http import streamablehttp_client 
from strands.tools.mcp.mcp_client import MCPClient
from src.mortgage_processor.utils.agent_core import get_token
import logging

def get_gateway_mcp_client(region: Optional[str],
                        client_id: str = "35j0m1mieai58f3k6heknnvltb", 
                        client_secret: str = "idjpa3ep9pve1fsfg03i3lei8njtd6j2k0e78rg6suje5qf6bqp", 
                        resource_server_id: str = "sample-agentcore-gateway-id", 
                        user_pool_id: str = 'us-east-1_bHASSuci6', 
                        gateway_url: str = "https://testgwforlambda-oivlepaosr.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp") -> MCPClient:

    region = region if region else os.environ.get('AWS_REGION','us-east-1')
    scopeString = f"{resource_server_id}/gateway:read {resource_server_id}/gateway:write"

    logging.info("Requesting the access token from Amazon Cognito authorizer")
    token_response = get_token(user_pool_id, client_id, client_secret, scopeString, region)
    token = token_response["access_token"]
    logging.info("Token response: %s", token)

    def create_streamable_http_transport():
        return streamablehttp_client(gateway_url,headers={"Authorization": f"Bearer {token}"})

    mcp_client = MCPClient(create_streamable_http_transport)
    return mcp_client