import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.types.content import ContentBlock
from mortgage_processor.agents.main_agent import invoke_graph
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

    content_blocks = [
        ContentBlock(text="""
                    Validate and store the mortgage application:
                    """),
        ContentBlock(text=json.dumps(prompt)),
    ]

    result = await invoke_graph(content_blocks)

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