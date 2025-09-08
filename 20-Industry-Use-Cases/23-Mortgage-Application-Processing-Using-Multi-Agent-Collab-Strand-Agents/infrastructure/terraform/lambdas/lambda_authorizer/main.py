import os
from typing import Dict, Any
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger(service="authorizer")

API_KEY = os.environ["API_KEY"]

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    headers: dict = event.get("headers", {})
    api_key = headers.get("api_key")
    
    effect = "Allow" if api_key == API_KEY else "Deny"
    
    return generatePolicy('user', effect, event['routeArn'], "Authorized : Valid api_key Header")

def generatePolicy(principalId, effect, resource, message):
    authResponse = {
        'principalId': principalId,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        },
        "context": {
            "errorMessage": message
        }
    }
    return authResponse