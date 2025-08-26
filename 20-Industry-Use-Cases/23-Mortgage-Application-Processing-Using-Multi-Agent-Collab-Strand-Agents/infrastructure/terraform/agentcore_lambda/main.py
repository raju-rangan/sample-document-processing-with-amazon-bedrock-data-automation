import json
import boto3
import os
from typing import Dict, Any
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN")
AGENT_ENDPOINT_NAME = os.environ.get("AGENT_ENDPOINT_NAME")

logger = Logger(service="agentcore-service")


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    res = invoke_agentcore(prompt="")
    return response(200, {'message': res})

def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }

def invoke_agentcore(prompt: str) -> str:
    client = boto3.client('bedrock-agentcore')
    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        qualifier=AGENT_ENDPOINT_NAME,
        payload=prompt
    )
    return response