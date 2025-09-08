from strands import Agent
from strands.multiagent import GraphBuilder
from strands.multiagent.graph import GraphState
from mortgage_processor.agents.storage_agent import bedrock_model, STORAGE_AGENT_SYSTEM_PROMPT
import os
import json
from mortgage_processor.mcp.mcp_client import get_gateway_mcp_client
from mortgage_processor.agents.validation_agent import validation_expert, val_expert
from mortgage_processor.agents.extraction_agent import extraction_expert


def only_if_validation_successful(state: GraphState):
    """Only traverse if validation was successful."""
    validation_node = state.results.get("validation")
    if not validation_node:
        return False

    result = str(validation_node.result)
    return "1" in result

def only_if_validation_not_successful(state: GraphState):
    """Only traverse if validation was successful."""
    validation_node = state.results.get("validation")
    if not validation_node:
        return False

    result = str(validation_node.result)
    return "1" not in result
    

async def invoke_graph(prompt):
    gateway_mcp_client = get_gateway_mcp_client(region=os.environ.get('AWS_REGION','us-east-1'))
    with gateway_mcp_client:
        gateway_tools = gateway_mcp_client.list_tools_sync()

        storage_agent = Agent(
            name="storage_agent",
            system_prompt=STORAGE_AGENT_SYSTEM_PROMPT,
            model=bedrock_model,
            tools=[gateway_tools],
        )

        builder = GraphBuilder()
        
        # builder.add_node(extraction_expert, "extraction")
        # builder.add_node(val_expert, "validation")
        builder.add_node(storage_agent, "storage")

        # builder.add_edge("extraction", "validation")
        # builder.add_edge("validation", "extraction")
        # builder.add_edge("validation", "storage", condition=only_if_validation_successful)

        builder.set_entry_point("storage")

        builder.set_max_node_executions(20)
        builder.reset_on_revisit()
        graph = builder.build()
        result = await graph.invoke_async(prompt)
        return result