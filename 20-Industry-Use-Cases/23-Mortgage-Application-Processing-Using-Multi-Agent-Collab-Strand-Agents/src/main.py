from strands import Agent
from bda_agent_assistant import bda_agent
from dynamo_agent_assistant import dynamodb_agent
from kb_retrieval_assistant import kb_retrieval_agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.multiagent import Swarm

import logging


logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

app = BedrockAgentCoreApp(debug=True)

agents = [bda_agent,dynamodb_agent,kb_retrieval_agent]

swarm = Swarm(
    nodes=agents,
    max_handoffs=20,
    max_iterations=20,
    execution_timeout=900.0,  # 15 minutes
    node_timeout=300.0,       # 5 minutes per agent
    repetitive_handoff_detection_window=8,  # There must be >= 3 unique agents in the last 8 handoffs
    repetitive_handoff_min_unique_agents=3
)


@app.entrypoint
async def process_mortgage(payload):
    s3_uri = payload.get(
        "s3_uri", "No S3 URI found in input, please provide a JSON payload with s3_uri key pointing to the PDF document"
    )

    result = swarm(s3_uri)

    print(f"Status: {result.status}")
    print(f"Node history: {[node.node_id for node in result.node_history]}")

    return { "result": result }
    
if __name__ == '__main__':
    app.run()