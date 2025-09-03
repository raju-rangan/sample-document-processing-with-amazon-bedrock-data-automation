import json
import os
from boto3.session import Session
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
import time
from smart_open import open
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

INPUT_S3_BUCKET = os.environ["INPUT_S3_BUCKET"]
OUTPUT_S3_BUCKET = os.environ["OUTPUT_S3_BUCKET"]
BDA_PROJECT_ARN = os.environ["BDA_PROJECT_ARN"]
BDA_PROFILE_ARN = os.environ["BDA_PROFILE_ARN"]
AGENT_RUNTIME_ARN = os.environ["AGENT_RUNTIME_ARN"]
AGENT_ENDPOINT_NAME = os.environ["AGENT_ENDPOINT_NAME"]

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
                    invocation_arn = trigger_bedrock_data_automation(
                        object_key = object_key,
                        input_s3_bucket=INPUT_S3_BUCKET,
                        output_s3_bucket=OUTPUT_S3_BUCKET,
                        project_arn=BDA_PROJECT_ARN,
                        profile_arn=BDA_PROFILE_ARN,
                    )
                    result = wait_for_bedrock_data_automation(invocation_arn=invocation_arn)

                    s3_uri = result["outputConfiguration"].get("s3Uri")
                    with open(s3_uri) as f:
                        json_string = json.load(f)
                        res = get_bedrock_data_automation_results(job_metadata=json_string)
                    agent_core_result = invoke_agentcore(prompt=json.dumps(res))
                    processed_objects.append(result)
                else:
                    logger.info(f"Skipping non-creation event: {event_name}")
        return response(200, {'message': 'request accepted', 'objects': processed_objects, 'invocation_arn': invocation_arn, 'agent_core_result': agent_core_result})
        
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


def invoke_agentcore(prompt: str) -> str:
    logger.info(f"Invoking Agentcore {AGENT_RUNTIME_ARN} with prompt: {prompt}")

    client = boto3.client('bedrock-agentcore')

    payload = json.dumps({"prompt": prompt}).encode()

    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        qualifier=AGENT_ENDPOINT_NAME,
        payload=payload
    )
    return response

def get_bedrock_data_automation_results(job_metadata: dict) -> dict:
    output_metadata = job_metadata["output_metadata"][0]
    segment_metadata = output_metadata["segment_metadata"]
    inference_results = {}
    for segment in segment_metadata:
        custom_output_status = segment["custom_output_status"]
        if custom_output_status == "MATCH":
            custom_output_path = segment["custom_output_path"]
            with open(custom_output_path) as f:
                json_string = json.load(f)
                document_class = json_string["document_class"]["type"]
                inference_result = json_string["inference_result"]
                inference_results[document_class] = inference_result
        elif custom_output_status == "NO_MATCH":
            standard_output_path = segment["standard_output_path"]
            with open(standard_output_path) as f:
                json_string = json.load(f)
                pages = json_string["pages"]
                for page in pages:
                    page_index = page["page_index"]
                    inference_result = page["representation"]["markdown"]
                    inference_results[f"page-{page_index}"] = inference_result
    return inference_results


def trigger_bedrock_data_automation(
    object_key: str,
    input_s3_bucket: str,
    output_s3_bucket: str,
    project_arn: str,
    profile_arn: Optional[str],
    region: Optional[str] = None,
) -> str:
    
    region = region or os.getenv("AWS_REGION") or Session().region_name
    boto_session = Session(region_name=region)
    client = boto_session.client("bedrock-data-automation-runtime")
    logger.info(f"Invoking Bedrock Data Automation project: {project_arn} in region {region}")

    payload: Dict[str, Any] = {
        "dataAutomationConfiguration": {
            "dataAutomationProjectArn": project_arn
        },
        "inputConfiguration": {
            "s3Uri": f's3://{input_s3_bucket}/{object_key}'
        },
        "outputConfiguration": {
            "s3Uri": f's3://{output_s3_bucket}/results'
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
    

def wait_for_bedrock_data_automation(
    invocation_arn: str,
    region: Optional[str] = None,
    poll_interval: int = 1,
    max_wait_time: int = 3600
) -> Dict[str, Any]:
    region = region or os.getenv("AWS_REGION") or Session().region_name
    boto_session = Session(region_name=region)
    client = boto_session.client("bedrock-data-automation-runtime")
    
    logger.info(f"Waiting for Bedrock Data Automation invocation: {invocation_arn}")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = client.get_data_automation_status(invocationArn=invocation_arn)
            
            status = response.get("status")
            logger.info(f"Current status: {status}")
            
            if status == "Success":
                logger.info("Bedrock Data Automation job completed successfully")
                print(f"✅ SUCCESS: Bedrock Data Automation job completed")
                print(f"Invocation ARN: {invocation_arn}")
                print(f"Final Status: {status}")
                
                if "outputConfiguration" in response:
                    output_s3_uri = response["outputConfiguration"].get("s3Uri")
                    if output_s3_uri:
                        print(f"Output Location: {output_s3_uri}")
                
                return response
                
            elif status in ["ServiceError", "ClientError"]:
                error_message = response.get("errorMessage", "Unknown error")
                error_type = response.get("errorType", "Unknown error type")
                logger.error(f"Bedrock Data Automation job failed: {error_type} - {error_message}")
                print(f"❌ FAILED: Bedrock Data Automation job failed")
                print(f"Invocation ARN: {invocation_arn}")
                print(f"Error Type: {error_type}")
                print(f"Error Message: {error_message}")
                raise RuntimeError(f"Bedrock Data Automation job failed: {error_type} - {error_message}")
                
            elif status in ["Created", "InProgress"]:
                logger.info(f"Job still in progress (status: {status}), waiting {poll_interval} seconds...")
                time.sleep(poll_interval)
                continue
                
            else:
                logger.warning(f"Unknown status received: {status}")
                print(f"⚠️  WARNING: Unknown status: {status}")
                time.sleep(poll_interval)
                continue
                
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            if error_code == "ResourceNotFoundException":
                logger.error(f"Invocation not found: {invocation_arn}")
                print(f"❌ ERROR: Invocation not found: {invocation_arn}")
                raise RuntimeError(f"Invocation not found: {invocation_arn}")
            else:
                logger.error(f"Error checking status: {error_message}")
                print(f"❌ ERROR: Failed to check status: {error_message}")
                raise RuntimeError(f"Failed to check job status: {error_message}")
                
        except Exception as e:
            logger.error(f"Unexpected error while waiting for job: {e}")
            print(f"❌ UNEXPECTED ERROR: {e}")
            raise RuntimeError(f"Unexpected error while waiting for job: {e}")
            
    elapsed_time = time.time() - start_time
    logger.error(f"Job timed out after {elapsed_time:.0f} seconds")
    print(f"⏰ TIMEOUT: Job did not complete within {max_wait_time} seconds")
    print(f"Invocation ARN: {invocation_arn}")
    print(f"Last known status: {status if 'status' in locals() else 'Unknown'}")
    raise RuntimeError(f"Job timed out after {max_wait_time} seconds")