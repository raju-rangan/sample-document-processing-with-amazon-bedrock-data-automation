import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mortgage_processor.agents.graph import invoke_graph
import os

import logging
logging_level = os.environ.get("LOGGING_LEVEL", logging.INFO)
logging.getLogger("strands").setLevel(logging_level)

logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

app = BedrockAgentCoreApp()

@app.entrypoint
async def process_mortgage(payload):
    prompt = payload.get(
        "prompt", "No prompt"
    )

    result = await invoke_graph(prompt)

    response = {
        "Status": str(result.status),
        "Execution order": str([node.node_id for node in result.execution_order])
    }

    for node in result.execution_order:
        response[node.node_id] = str(result.results[node.node_id].result)
    
    logging.info(f"response: {response}")
    return json.dumps(response, indent=2)
    
if __name__ == '__main__':
    app.run()