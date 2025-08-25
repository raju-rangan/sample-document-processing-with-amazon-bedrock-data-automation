import json
from pathlib import Path
from typing import Any, Dict, Tuple
import mortgage_processor.utils.agent_core as utils
import boto3
import os
from botocore.exceptions import ClientError, ValidationError
from strands.models import BedrockModel
from mcp.client.streamable_http import streamablehttp_client 
from strands.tools.mcp.mcp_client import MCPClient
from strands import Agent
import logging
import yaml
import sys
import time

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
GATEWAY_NAME = "TestGWforLambda"
LAMBDA_FUNCTION_NAME = "mortgage-applications-crud"
TARGET_NAME = "MortgageCRUD"

USER_POOL_NAME = "sample-agentcore-gateway-pool"
RESOURCE_SERVER_ID = "sample-agentcore-gateway-id"
RESOURCE_SERVER_NAME = "sample-agentcore-gateway-name"
CLIENT_NAME = "sample-agentcore-gateway-client"
SCOPES = [
    {"ScopeName": "gateway:read", "ScopeDescription": "Read access"},
    {"ScopeName": "gateway:write", "ScopeDescription": "Write access"},
]

TOOL_SCHEMA_FILE = "mcp_api.yaml"

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


def create_gateway_role(gateway_name: str) -> str:
    role = utils.create_agentcore_gateway_role(gateway_name)
    return role["Role"]["Arn"]


def create_cognito(cognito) -> Tuple[str, str, str, str, str]:
    logging.info("Ensuring Cognito resources...")
    user_pool_id = utils.get_or_create_user_pool(cognito, USER_POOL_NAME)
    utils.get_or_create_resource_server(cognito, user_pool_id, RESOURCE_SERVER_ID, RESOURCE_SERVER_NAME, SCOPES)
    client_id, client_secret = utils.get_or_create_m2m_client(cognito, user_pool_id, CLIENT_NAME, RESOURCE_SERVER_ID)

    scope_string = f"{RESOURCE_SERVER_ID}/gateway:read {RESOURCE_SERVER_ID}/gateway:write"
    discovery_url = f"https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    return user_pool_id, client_id, client_secret, scope_string, discovery_url


def create_gateway(client, role_arn: str, authorizer_config: Dict[str, Any]) -> Tuple[str, str]:
    try:
        resp = client.create_gateway(
            name=GATEWAY_NAME,
            roleArn=role_arn,
            protocolType="MCP",
            authorizerType="CUSTOM_JWT",
            authorizerConfiguration=authorizer_config,
            description="AgentCore Gateway with AWS Lambda target type"
        )
        return resp["gatewayId"], resp["gatewayUrl"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            logging.info("Gateway exists, retrieving...")
            list_resp = client.list_gateways(maxResults=50)
            for gw in list_resp.get("items", []):
                if gw["name"] == GATEWAY_NAME:
                    get_resp = client.get_gateway(gatewayIdentifier=gw["gatewayId"])
                    return get_resp["gatewayId"], get_resp["gatewayUrl"]
        raise

def upload_api_spec_to_s3(bucket_name: str, api_file_path: str) -> str:
    session = boto3.session.Session()
    s3_client = session.client('s3')
    
    try:
        s3bucket = s3_client.create_bucket(
            Bucket=bucket_name
        )
        logging.info(f"Successfully created bucket")
        logging.debug(s3bucket)
    except Exception as e:
        logging.exception(e)
        raise e

    file_name = os.path.basename(api_file_path)
    object_key = f'specs/{file_name}'
    s3_uri = f's3://{bucket_name}/{object_key}'
    with open(api_file_path, 'rb') as file_data:
        response = s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=file_data)    
        logging.info(f"Successfully uploaded api spec to {s3_uri}")
        logging.debug(response)

    return s3_uri

def create_openapi_cred_provider(cred_provider_name: str, api_key: str) -> str:
    acps = boto3.client(service_name="bedrock-agentcore-control")
    
    try:
        response=acps.create_api_key_credential_provider(
            name=cred_provider_name,
            apiKey=api_key,
        )
    except acps.exceptions.ValidationException as e:
        logging.warning(f'{cred_provider_name} already exists')
        providers = acps.list_api_key_credential_providers(
            maxResults=10
        )['credentialProviders']
        for provider in providers:
            if provider['name'] == cred_provider_name:
                response = provider

    credentialProviderARN = response['credentialProviderArn']
    logging.info(f"Egress Credentials provider ARN, {credentialProviderARN}")
    return credentialProviderARN

def create_openapi_target(client, gateway_id: str, openapi_s3_uri: str, cred_provider_arn: str) -> str:
    openapi_target_config = {
        "mcp": {
            "openApiSchema": {
                "s3": {
                    "uri": openapi_s3_uri
                } 
            }
        }
    }
    api_key_credential_config = [
        {
            "credentialProviderType" : "API_KEY", 
            "credentialProvider": {
                "apiKeyCredentialProvider": {
                        "credentialParameterName": "api_key", # Replace this with the name of the api key name expected by the respective API provider. For passing token in the header, use "Authorization"
                        "providerArn": cred_provider_arn,
                        "credentialLocation":"HEADER", # Location of api key. Possible values are "HEADER" and "QUERY_PARAMETER".
                }
            }
        }
    ]

    try:
        resp = client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name=TARGET_NAME,
            description="Mortgage CRUD via openapi",
            targetConfiguration=openapi_target_config,
            credentialProviderConfigurations=api_key_credential_config
        )
        return resp["targetId"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            logging.info("Target exists, replacing...")
            items = client.list_gateway_targets(gatewayIdentifier=gateway_id)["items"]
            existing = next((t for t in items if t["name"] == TARGET_NAME), None)
            if existing:
                client.delete_gateway_target(gatewayIdentifier=gateway_id, targetId=existing["targetId"])
                resp = client.create_gateway_target(
                    gatewayIdentifier=gateway_id,
                    name=TARGET_NAME,
                    description="Mortgage CRUD via openapi",
                    targetConfiguration=openapi_target_config,
                    credentialProviderConfigurations=api_key_credential_config
                )
                return resp["targetId"]
        raise

def create_lambda_target(client, gateway_id: str, lambda_arn: str, tool_schema: Dict[str, Any]) -> str:
    lambda_target_config = {
        "mcp": {
            "lambda": {
                "lambdaArn": lambda_arn,
                "toolSchema": tool_schema
            }
        }
    }
    credential_config = [
        {"credentialProviderType": "GATEWAY_IAM_ROLE"}
        ]

    try:
        resp = client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name=TARGET_NAME,
            description="Mortgage Lambda Target using SDK",
            targetConfiguration=lambda_target_config,
            credentialProviderConfigurations=credential_config
        )
        return resp["targetId"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            logging.info("Target exists, replacing...")
            items = client.list_gateway_targets(gatewayIdentifier=gateway_id)["items"]
            existing = next((t for t in items if t["name"] == TARGET_NAME), None)
            if existing:
                client.delete_gateway_target(gatewayIdentifier=gateway_id, targetId=existing["targetId"])
                resp = client.create_gateway_target(
                    gatewayIdentifier=gateway_id,
                    name=TARGET_NAME,
                    description="Mortgage Lambda Target using SDK",
                    targetConfiguration=lambda_target_config,
                    credentialProviderConfigurations=credential_config
                )
                return resp["targetId"]
        raise


def get_lambda_arn(region: str, function_name: str) -> str:
    client = boto3.client("lambda", region_name=region)
    fn = client.get_function(FunctionName=function_name)
    return fn["Configuration"]["FunctionArn"]


def load_tool_schema() -> Dict[str, Any]:
    schema_path = Path(__file__).resolve().parent / TOOL_SCHEMA_FILE
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def get_bearer_token(user_pool_id: str, client_id: str, client_secret: str, scope_string: str) -> str:
    for attempt in range(1, 10):
        try:
            resp = utils.get_token(user_pool_id, client_id, client_secret, scope_string, REGION)
            return resp["access_token"]
        except Exception as e:
            logging.warning(f"Token fetch failed (attempt {attempt}): {e}")
            time.sleep(5)
    raise RuntimeError("Failed to retrieve token after retries.")


def run_agent_demo(gateway_url: str, token: str):
    if not all([MCPClient, streamablehttp_client, Agent, BedrockModel]):
        logging.info("Agent demo skipped (optional dependencies missing).")
        return

    def create_streamable_http_transport():
        return streamablehttp_client(gateway_url, headers={"Authorization": f"Bearer {token}"})

    model = BedrockModel(model_id="us.amazon.nova-pro-v1:0", temperature=0.0)

    with MCPClient(create_streamable_http_transport) as client:
        tools = client.list_tools_sync()
        agent = Agent(model=model, tools=tools)
        logging.info(f"Tools loaded: {agent.tool_names}")
        print(agent("Hi, can you list all tools available to you?"))
        print(agent("Hi, list all the information I need to create a new application"))


def main():
    script_path = os.path.abspath(__file__)
    print(script_path)
    script_dir = os.path.dirname(script_path)
    s3_uri = upload_api_spec_to_s3("amitzaf-mortgage-demo-bucket", os.path.join(script_dir, "openapi_spec.json"))

    # 1) Gateway IAM role
    role_arn = create_gateway_role("sample-lambdagateway")

    # 2) Cognito setup
    cognito = boto3.client("cognito-idp", region_name=REGION)
    user_pool_id, client_id, client_secret, scope_string, discovery_url = create_cognito(cognito)

    # 3) Gateway
    gateway_client = boto3.client("bedrock-agentcore-control", region_name=REGION)
    auth_config = {
        "customJWTAuthorizer": {
            "allowedClients": [client_id],
            "discoveryUrl": discovery_url
        }
    }
    gateway_id, gateway_url = create_gateway(gateway_client, role_arn, auth_config)

    # 4) Lambda target
    # lambda_arn = get_lambda_arn(REGION, LAMBDA_FUNCTION_NAME)
    # tool_schema = load_tool_schema()
    cred_provider_arn = create_openapi_cred_provider("MyAPIKey", "aaa")
    target_id = create_openapi_target(gateway_client, gateway_id, s3_uri, cred_provider_arn)
    # target_id = create_lambda_target(gateway_client, gateway_id, lambda_arn, tool_schema)

    # 5) Access token
    token = get_bearer_token(user_pool_id, client_id, client_secret, scope_string)

    # 6) Run optional agent demo
    run_agent_demo(gateway_url, token)

    # Final output (for other scripts)
    print(json.dumps({
        "credentialsProviderARN": cred_provider_arn,
        "gatewayId": gateway_id,
        "gatewayUrl": gateway_url,
        "targetId": target_id,
        "userPoolId": user_pool_id,
        "clientId": client_id
    }, indent=2))


if __name__ == "__main__":
    sys.exit(main())