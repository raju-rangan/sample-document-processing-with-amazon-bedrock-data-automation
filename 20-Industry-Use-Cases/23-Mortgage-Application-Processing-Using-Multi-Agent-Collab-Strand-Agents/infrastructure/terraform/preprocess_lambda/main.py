import json
import os
from boto3.session import Session
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

INPUT_S3_BUCKET = os.environ.get("INPUT_S3_BUCKET")
OUTPUT_S3_BUCKET = os.environ.get("OUTPUT_S3_BUCKET")

logger = Logger(service="mortgage-preprocess-service")


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda function to handle S3 events when new objects are added.
    
    Args:
        event: S3 event data containing Records with bucket and object information
        context: Lambda context object
    
    Returns:
        Dict containing processing results
    """
    try:
        processed_objects = []
        
        for record in event.get('Records', []):
            if record.get('eventSource') == 'aws:s3':
                s3_info = record.get('s3', {})
                bucket_name = s3_info.get('bucket', {}).get('name')
                object_key = s3_info.get('object', {}).get('key')
                object_size = s3_info.get('object', {}).get('size', 0)
                event_name = record.get('eventName', '')
                
                logger.info(
                    f"Processing S3 event",
                    extra={
                        "event_name": event_name,
                        "bucket_name": bucket_name,
                        "object_key": object_key,
                        "object_size": object_size
                    }
                )

                if event_name.startswith('ObjectCreated'):
                    processed_objects.append(object_key)
                else:
                    logger.info(f"Skipping non-creation event: {event_name}")
        return response(200, {'message': 'request accepted', 'objects': processed_objects})
        
    except Exception as e:
        logger.error(f"Error processing S3 event: {str(e)}", exc_info=True)
        return response(500, {"error": "Failed to process S3 event", 'message': str(e)})

def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }

def trigger_bedrock_data_automation(
    input_s3_uri: str,
    output_s3_uri: str,
    project_arn: str,
    region: Optional[str],
    profile_arn: Optional[str]
) -> str:
    """
    Triggers an Amazon Bedrock Data Automation job and returns the invocation ARN.

    Args:
        input_s3_uri (str): S3 URI of the input file(s) (e.g., 's3://bucket/path').
        output_s3_uri (str): S3 URI for the output results.
        project_arn (str): ARN of the Bedrock Data Automation project.
        region (str): AWS region override; falls back to environment or default.
        profile_arn (str): Optional data automation profile ARN, if required.

    Returns:
        str: The invocation ARN of the triggered job.

    Raises:
        RuntimeError: If the BDA invocation fails.
    """
    region = region or os.getenv("AWS_REGION") or Session().region_name
    boto_session = Session(region_name=region)
    client = boto_session.client("bedrock-data-automation")
    logger.info("Invoking Bedrock Data Automation job in region %s", region)

    payload: Dict[str, Any] = {
        "dataAutomationConfiguration": {
            "dataAutomationProjectArn": project_arn
        },
        "inputConfiguration": {
            "s3Uri": input_s3_uri
        },
        "outputConfiguration": {
            "s3Uri": output_s3_uri
        }
    }

    if profile_arn:
        payload["dataAutomationProfileArn"] = profile_arn

    try:
        response = client.invoke_data_automation_async(**payload)
        invocation_arn = response.get("invocationArn")
        if not invocation_arn:
            raise RuntimeError("Invocation ARN not returned in response.")
        logger.info("Bedrock Data Automation job started. Invocation ARN: %s", invocation_arn)
        return invocation_arn
    except ClientError as e:
        logger.error("Failed to invoke Bedrock Data Automation: %s", e)
        raise RuntimeError("Bedrock Data Automation invocation failed") from e