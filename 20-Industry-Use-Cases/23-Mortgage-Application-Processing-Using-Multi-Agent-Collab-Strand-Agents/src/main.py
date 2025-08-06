from data_extraction_agent import data_extraction_agent
from storage_agent import storage_agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.multiagent import Swarm
from strands.types.content import ContentBlock
import boto3
import os

import logging


logging.getLogger("strands.multiagent").setLevel(logging.INFO)

logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

main_log = logging.getLogger("orchestration")

app = BedrockAgentCoreApp()

agents = [data_extraction_agent, storage_agent]

swarm = Swarm(
    nodes=agents,
    max_handoffs=20,
    max_iterations=20,
    execution_timeout=900.0,  # 15 minutes
    node_timeout=300.0,       # 5 minutes per agent
    repetitive_handoff_detection_window=2,
    repetitive_handoff_min_unique_agents=2
)

os.makedirs('./files', exist_ok=True)

session = boto3.Session(region_name=os.environ.get('AWS_REGION', 'us-east-1'))
s3_client = session.client('s3')

@app.entrypoint
async def process_mortgage(payload):
    bucket = payload.get(
        "bucket", "No prompt"
    )
    key = payload.get(
        "key", "No prompt"
    )

    local_path = f'/app/files/{hash(key)}.pdf'
    if not os.path.exists(local_path):
        s3_client.download_file(bucket, key, local_path)

    main_log.info(f"Downloaded S3 object to: {local_path}")
        
    content_blocks = [
        ContentBlock(text="""
                    Analyze the mortgage document at the given file path and extract key information,
                    then STORE this data in a structured and unstructured format with appropriate categorization and indexing for future retrieval:
                    """),
        ContentBlock(text=local_path),
    ]

    result = await swarm.invoke_async(content_blocks)

    response = {}
    response["Status"] = str(result.status)
    response["NodeHistory"] = str(result.node_history)

    for node in result.node_history:
        response[node.node_id] = result.results[node.node_id].result

    return response
    
if __name__ == '__main__':
    app.run()