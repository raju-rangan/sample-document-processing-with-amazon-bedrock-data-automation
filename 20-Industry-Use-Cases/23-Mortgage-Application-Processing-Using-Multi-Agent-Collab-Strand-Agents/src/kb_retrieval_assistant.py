from strands import Agent, tool
from strands import Agent
from strands.tools.mcp import MCPClient
import boto3
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters


KB_RETRIEVAL_AGENT_ASSISTANT_SYSTEM_PROMPT = """

"""


@tool
def kb_retrieval_assistant(query: str) -> str:
    """
    Process and respond to Bedrock knowledge bases retrieval requests.
    
    Args:
        query: The user's Bedrock knowledge bases retrieval request
        
    Returns:
        A detailed response
    """
    session = boto3.Session(
        region_name='us-west-2',
    )

    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        boto_session=session,
    )

    kb_retrieval_mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="uvx", 
            args=["awslabs.bedrock-kb-retrieval-mcp-server@latest"]
        )
    ))

    # Format the query for the agent with clear instructions
    formatted_query = f"Address this Bedrock knowledge bases retrieval request: {query}"
    
    try:
        print("Routed to KB Retrieval Agent Assistant")
        # Create the agent with relevant tools
        kb_retrieval_agent = Agent(
            system_prompt=KB_RETRIEVAL_AGENT_ASSISTANT_SYSTEM_PROMPT,
            model=bedrock_model,
            tools=kb_retrieval_mcp_client.list_tools_sync(),
        )
        agent_response = kb_retrieval_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response
        
        return "I apologize, but I couldn't process your Bedrock knowledge bases retrieval request."
    except Exception as e:
        return f"Error processing your Bedrock knowledge bases retrieval agent query: {str(e)}"