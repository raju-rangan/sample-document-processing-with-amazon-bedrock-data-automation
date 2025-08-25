import json
from src.mortgage_processor.agents.data_extraction_agent import DATA_EXTRACTION_SYSTEM_PROMPT, bda_mcp_client
from strands import Agent
from src.mortgage_processor.agents.validation_agent import VALIDATION_AGENT_SYSTEM_PROMPT
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.types.content import ContentBlock
import boto3
from strands.multiagent import GraphBuilder
from src.mortgage_processor.agents.storage_agent import bedrock_model, STORAGE_AGENT_SYSTEM_PROMPT, aws_api_mcp_client
import os
from src.mortgage_processor.mcp.mcp_client import get_gateway_mcp_client

import logging


logging.getLogger("strands").setLevel(logging.INFO)

logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

app = BedrockAgentCoreApp()

async def invoke_graph(prompt):
    gateway_mcp_client = get_gateway_mcp_client(region=os.environ.get('AWS_REGION','us-east-1'))
    with gateway_mcp_client, aws_api_mcp_client, bda_mcp_client:
        gateway_tools = gateway_mcp_client.list_tools_sync()
        aws_api_tools = aws_api_mcp_client.list_tools_sync()
        bda_mcp_tools = bda_mcp_client.list_tools_sync()

        data_extraction_agent = Agent( 
            name="data_extraction_agent",
            system_prompt=DATA_EXTRACTION_SYSTEM_PROMPT,
            model=bedrock_model,
            tools=[bda_mcp_tools],
        )

        validation_agent = Agent(
            name="validation_agent",
            system_prompt=VALIDATION_AGENT_SYSTEM_PROMPT,
            model=bedrock_model,
        )

        storage_agent = Agent(
            name="storage_agent",
            system_prompt=STORAGE_AGENT_SYSTEM_PROMPT,
            model=bedrock_model,
            tools=[gateway_tools],
        )

        builder = GraphBuilder()

        builder.add_node(data_extraction_agent, "data_extraction_agent")
        builder.add_node(storage_agent, "storage_agent")
        # builder.add_node(validation_agent, "validation_agent")

        builder.add_edge("data_extraction_agent", "storage_agent")
        # builder.add_edge("validation_agent", "storage_agent")

        builder.set_entry_point("data_extraction_agent")

        graph = builder.build()
        result = await graph.invoke_async(prompt)
        return result

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

    content_blocks = [
        ContentBlock(text="""
                    ANALYZE and STORE the mortgage document at the given file path:
                    """),
        ContentBlock(text=local_path),
    ]

    result = await invoke_graph(content_blocks)

    response = {}
    response["Status"] = str(result.status)
    response["Execution order"] = str([node.node_id for node in result.execution_order])

    for node in result.execution_order:
        response[node.node_id] = str(result.results[node.node_id].result)

    return json.dumps(response, indent=2)
    
if __name__ == '__main__':
    app.run()