import os
from typing import Dict, Any
from aws_lambda_powertools.utilities.typing import LambdaContext

API_KEY = os.environ["API_KEY"]

def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    headers: dict = event.get("headers", {})
    api_key = headers.get("api_key")
    
    effect = "Allow" if api_key == API_KEY else "Deny"
    
    policy = {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": event.get("methodArn")
                }
            ]
        }
    }
    return policy