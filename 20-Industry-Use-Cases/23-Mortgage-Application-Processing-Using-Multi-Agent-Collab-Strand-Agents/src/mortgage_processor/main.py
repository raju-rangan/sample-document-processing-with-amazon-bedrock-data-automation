import json
import logging
import os
from typing import Dict, Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mortgage_processor.agents.graph import invoke_graph

logging_level = os.environ.get("LOGGING_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, logging_level.upper()),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)
logging.getLogger("strands").setLevel(logging_level)

app = BedrockAgentCoreApp()

@app.entrypoint
async def process_mortgage(payload: Dict[str, Any]) -> str:
    """
    Process mortgage application using multi-agent workflow.
    
    Args:
        payload: Input payload containing prompt and other parameters
        
    Returns:
        JSON string with processing results
    """
    try:
        prompt = payload.get("prompt", "No prompt provided")
        logger.info(f"Processing mortgage application with prompt: {prompt[:100]}...")
        
        result = await invoke_graph(prompt)
        
        response = {
            "status": str(result.status),
            "execution_order": [node.node_id for node in result.execution_order],
        }
        
        for node in result.execution_order:
            if node.node_id in result.results:
                response[node.node_id] = str(result.results[node.node_id].result)
        
        logger.info(f"Successfully processed mortgage application. Status: {result.status}")
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error processing mortgage application: {str(e)}", exc_info=True)
        error_response = {
            "status": "error",
            "error_message": str(e),
            "execution_order": []
        }
        return json.dumps(error_response, indent=2)

if __name__ == '__main__':
    logger.info("Starting Mortgage Processor application...")
    app.run()