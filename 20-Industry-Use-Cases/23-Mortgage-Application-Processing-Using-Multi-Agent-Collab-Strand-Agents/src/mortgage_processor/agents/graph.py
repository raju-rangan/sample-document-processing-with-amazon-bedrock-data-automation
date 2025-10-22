from strands import Agent
from strands.multiagent import GraphBuilder
from strands.models import BedrockModel
from mortgage_processor.agents.storage_agent import STORAGE_AGENT_SYSTEM_PROMPT
from mortgage_processor.agents.extraction_agent import EXTRACTION_AGENT_SYSTEM_PROMPT
import os
import boto3
from mortgage_processor.mcp.mcp_client import get_gateway_mcp_client


async def invoke_graph(prompt: str):
    REGION = os.environ.get('AWS_REGION','us-east-1')

    gateway_mcp_client = get_gateway_mcp_client(region=REGION)

    session = boto3.Session(
        region_name=REGION,
    )

    with gateway_mcp_client:
        gateway_tools = gateway_mcp_client.list_tools_sync()

        extraction_model = BedrockModel(
            model_id="us.anthropic.claude-opus-4-20250514-v1:0",
            temperature=0.0,
            boto_session=session,
        )

        extraction_agent = Agent(
            name="extraction_agent",
            system_prompt=EXTRACTION_AGENT_SYSTEM_PROMPT,
            model=extraction_model,
        )
        

        storage_model = BedrockModel(
            model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
            temperature=0.0,
            boto_session=session,
        )

        storage_agent = Agent(
            name="storage_agent",
            system_prompt=STORAGE_AGENT_SYSTEM_PROMPT,
            model=storage_model,
            tools=[gateway_tools],
        )

        builder = GraphBuilder()
        
        builder.add_node(extraction_agent, "extraction")
        builder.add_node(storage_agent, "storage")

        builder.add_edge("extraction", "storage")

        builder.set_entry_point("extraction")

        graph = builder.build()
        result = await graph.invoke_async(prompt)
        return result