import json
import boto3
from boto3 import Session
import os
from typing import Dict, Any
from smart_open import open
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

AGENT_RUNTIME_ARN = os.environ["AGENT_RUNTIME_ARN"]
AGENT_ENDPOINT_NAME = os.environ["AGENT_ENDPOINT_NAME"]

logger = Logger(service="agentcore-service")


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    output_s3_location: dict = event['detail']['output_s3_location']
    s3_bucket: str = output_s3_location['s3_bucket']
    name: str = output_s3_location['name']

    result_file = name.rsplit('/', 1)[0]
    with open(f"s3://{s3_bucket}/{result_file}/job_metadata.json") as f:
        metadata = json.load(f)
        results = get_bedrock_data_automation_results(job_metadata=metadata)
        
    agentcore_response = invoke_agentcore(prompt=json.dumps(results))

    if "text/event-stream" in agentcore_response.get("contentType", ""):
        content = []
        for line in agentcore_response["response"].iter_lines(chunk_size=10):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    logger.info(line)
                    content.append(line)
            logger.info("\nComplete response:", "\n".join(content))

    elif agentcore_response.get("contentType") == "application/json":
        content = []
        for chunk in agentcore_response.get("response", []):
            content.append(chunk.decode('utf-8'))
        logger.info(json.loads(''.join(content)))
    
    else:
        logger.info(agentcore_response)

    return response(200, {'message': agentcore_response})


def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }


def invoke_agentcore(prompt: str) -> dict:
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