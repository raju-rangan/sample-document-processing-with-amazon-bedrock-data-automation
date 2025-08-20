import utils
import boto3
import os
from botocore.exceptions import ClientError
from strands.models import BedrockModel
from mcp.client.streamable_http import streamablehttp_client 
from strands.tools.mcp.mcp_client import MCPClient
from strands import Agent
import logging

#### Create an IAM role for the Gateway to assume
agentcore_gateway_iam_role = utils.create_agentcore_gateway_role("sample-lambdagateway")
print("Agentcore gateway role ARN: ", agentcore_gateway_iam_role['Role']['Arn'])

#### Creating Cognito User Pool 
REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
USER_POOL_NAME = "sample-agentcore-gateway-pool"
RESOURCE_SERVER_ID = "sample-agentcore-gateway-id"
RESOURCE_SERVER_NAME = "sample-agentcore-gateway-name"
CLIENT_NAME = "sample-agentcore-gateway-client"
SCOPES = [
    {"ScopeName": "gateway:read", "ScopeDescription": "Read access"},
    {"ScopeName": "gateway:write", "ScopeDescription": "Write access"}
]
scopeString = f"{RESOURCE_SERVER_ID}/gateway:read {RESOURCE_SERVER_ID}/gateway:write"

cognito = boto3.client("cognito-idp", region_name=REGION)

print("Creating or retrieving Cognito resources...")
user_pool_id = utils.get_or_create_user_pool(cognito, USER_POOL_NAME)
print(f"User Pool ID: {user_pool_id}")

utils.get_or_create_resource_server(cognito, user_pool_id, RESOURCE_SERVER_ID, RESOURCE_SERVER_NAME, SCOPES)
print("Resource server ensured.")

client_id, client_secret  = utils.get_or_create_m2m_client(cognito, user_pool_id, CLIENT_NAME, RESOURCE_SERVER_ID)
print(f"Client ID: {client_id}")
print(f"Client Secret: {client_secret}")

# Get discovery URL  
cognito_discovery_url = f'https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration'
print(cognito_discovery_url)

#### CreateGateway with Cognito authorizer without CMK. Use the Cognito user pool created in the previous step
gateway_client = boto3.client('bedrock-agentcore-control', region_name = os.environ['AWS_DEFAULT_REGION'])
auth_config = {
    "customJWTAuthorizer": { 
        "allowedClients": [client_id],  # Client MUST match with the ClientId configured in Cognito. Example: 7rfbikfsm51j2fpaggacgng84g
        "discoveryUrl": cognito_discovery_url
    }
}

gateway_name='TestGWforLambda'
gatewayID: str
gatewayURL: str

try:
    create_response = gateway_client.create_gateway(name='TestGWforLambda',
        roleArn = agentcore_gateway_iam_role['Role']['Arn'], # The IAM Role must have permissions to create/list/get/delete Gateway 
        protocolType='MCP',
        authorizerType='CUSTOM_JWT',
        authorizerConfiguration=auth_config, 
        description='AgentCore Gateway with AWS Lambda target type'
    )
    print(f'create_response: {create_response}')
    # Retrieve the GatewayID used for GatewayTarget creation
    gatewayID = create_response["gatewayId"]
    gatewayURL = create_response["gatewayUrl"]
except ClientError as e:
    if e.response['Error']['Code'] == 'ConflictException':
        print(f"Gateway already exists")
        list_response = gateway_client.list_gateways(maxResults=5)
        for gateway in list_response['items']:
            if gateway['name'] == gateway_name:
                get_response = gateway_client.get_gateway(
                    gatewayIdentifier=gateway["gatewayId"]
                )
                gatewayID = get_response["gatewayId"]
                gatewayURL = get_response["gatewayUrl"]
    else:
        raise e

print(f'gatewayID: {gatewayID}')
print(f'gatewayUrl: {gatewayURL}')

# Get Lambda ARN by function name
lambda_client = boto3.client('lambda', region_name=REGION)
lambda_function = lambda_client.get_function(FunctionName='mortgage-applications-crud')
lambda_arn = lambda_function['Configuration']['FunctionArn']

lambda_target_config = {
"mcp": {
        "lambda": {
            "lambdaArn": lambda_arn,
            "toolSchema": {
        "inlinePayload": [
            {
                "name": "create_application",
                "description": "Create a new application",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "httpMethod": {
                            "type": "string",
                            "description": "HTTP method for the request (use POST)"
                        },
                        "body": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the application"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Description of the application"
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Initial status of the application (active, inactive, or pending)"
                                },
                                "version": {
                                    "type": "string",
                                    "description": "Version of the application"
                                },
                                "configuration": {
                                    "type": "object",
                                    "description": "Application-specific configuration data"
                                }
                            },
                            "required": ["name"]
                        }
                    },
                    "required": ["httpMethod", "body"]
                }
            },
            {
                "name": "get_application",
                "description": "Get a specific application by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "httpMethod": {
                            "type": "string",
                            "description": "HTTP method for the request (use GET)"
                        },
                        "pathParameters": {
                            "type": "object",
                            "properties": {
                                "application_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the application"
                                }
                            },
                            "required": ["application_id"]
                        }
                    },
                    "required": ["httpMethod", "pathParameters"]
                }
            },
            {
                "name": "list_applications",
                "description": "List all applications with optional filtering and pagination",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "httpMethod": {
                            "type": "string",
                            "description": "HTTP method for the request (use GET)"
                        },
                        "queryStringParameters": {
                            "type": "object",
                            "properties": {
                                "limit": {
                                    "type": "string",
                                    "description": "Maximum number of applications to return"
                                },
                                "offset": {
                                    "type": "string",
                                    "description": "Number of applications to skip for pagination"
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Filter applications by status"
                                },
                                "search": {
                                    "type": "string",
                                    "description": "Search applications by name or description"
                                }
                            }
                        }
                    },
                    "required": ["httpMethod"]
                }
            },
            {
                "name": "update_application",
                "description": "Update an existing application",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "httpMethod": {
                            "type": "string",
                            "description": "HTTP method for the request (use PUT)"
                        },
                        "pathParameters": {
                            "type": "object",
                            "properties": {
                                "application_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the application"
                                }
                            },
                            "required": ["application_id"]
                        },
                        "body": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the application"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Description of the application"
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Status of the application (active, inactive, or pending)"
                                },
                                "version": {
                                    "type": "string",
                                    "description": "Version of the application"
                                },
                                "configuration": {
                                    "type": "object",
                                    "description": "Application-specific configuration data"
                                }
                            }
                        }
                    },
                    "required": ["httpMethod", "pathParameters", "body"]
                }
            },
            {
                "name": "delete_application",
                "description": "Delete an application by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "httpMethod": {
                            "type": "string",
                            "description": "HTTP method for the request (use DELETE)"
                        },
                        "pathParameters": {
                            "type": "object",
                            "properties": {
                                "application_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the application"
                                }
                            },
                            "required": ["application_id"]
                        }
                    },
                    "required": ["httpMethod", "pathParameters"]
                }
            }
        ]
    }
        }
    }
}



credential_config = [ 
    {
        "credentialProviderType" : "GATEWAY_IAM_ROLE"
    }
]
targetname='MortgageLambdaUsingSDK'

try:
    response = gateway_client.create_gateway_target(
        gatewayIdentifier=gatewayID,
        name=targetname,
        description='Mortgage Lambda Target using SDK',
        targetConfiguration=lambda_target_config,
        credentialProviderConfigurations=credential_config)
    print(f"Gateway target created: {response['targetId']}")
except ClientError as e:
    if e.response['Error']['Code'] == 'ConflictException':
        targets = gateway_client.list_gateway_targets(gatewayIdentifier=gatewayID)['items']
        existing_target = next((t for t in targets if t['name'] == targetname), None)
        
        if existing_target:
            gateway_client.delete_gateway_target(
                gatewayIdentifier=gatewayID,
                targetId=existing_target['targetId']
            )
            print(f"Replaced existing gateway target: {existing_target['targetId']}")
            
            response = gateway_client.create_gateway_target(
                gatewayIdentifier=gatewayID,
                name=targetname,
                description='Mortgage Lambda Target using SDK',
                targetConfiguration=lambda_target_config,
                credentialProviderConfigurations=credential_config)
            print(f"Gateway target created: {response['targetId']}")
    else:
        raise e

#### Request the access token from Amazon Cognito for inbound authorization
print("Requesting the access token from Amazon Cognito authorizer...May fail for some time till the domain name propogation completes")
token_response = utils.get_token(user_pool_id, client_id, client_secret, scopeString, REGION)
token = token_response["access_token"]
print("Token response:", token)

def create_streamable_http_transport():
    return streamablehttp_client(gatewayURL,headers={"Authorization": f"Bearer {token}"})

client = MCPClient(create_streamable_http_transport)

yourmodel = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    temperature=0.0,
)

# Configure the root strands logger. Change it to DEBUG if you are debugging the issue.
logging.getLogger("strands").setLevel(logging.DEBUG)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()]
)

with client:
    tools = client.list_tools_sync()
    agent = Agent(model=yourmodel,tools=tools) ## you can replace with any model you like
    print(f"Tools loaded in the agent are {agent.tool_names}")
    agent("Hi , can you list all tools available to you")