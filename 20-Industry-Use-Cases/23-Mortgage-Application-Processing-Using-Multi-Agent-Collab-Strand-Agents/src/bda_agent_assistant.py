from strands import Agent, tool
from strands import Agent
from strands.tools.mcp import MCPClient
import boto3
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters


BDA_AGENT_ASSISTANT_SYSTEM_PROMPT = """

"""


@tool
def bda_agent_assistant(query: str) -> str:
    """
    Process and respond to bedrock data automation requests.
    
    Args:
        query: The user's bedrock data automation request
        
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

    bda_mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="uvx", 
            args=["awslabs.aws-bedrock-data-automation-mcp-server@latest"]
        )
    ))

    # Format the query for the agent with clear instructions
    formatted_query = f"Address this bedrock data automation request: {query}"
    
    try:
        print("Routed to BDA Agent Assistant")
        # Create the agent with relevant tools
        bda_agent = Agent(
            system_prompt=BDA_AGENT_ASSISTANT_SYSTEM_PROMPT,
            model=bedrock_model,
            tools=bda_mcp_client.list_tools_sync(),
        )
        agent_response = bda_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response
        
        return "I apologize, but I couldn't process your bda request."
    except Exception as e:
        return f"Error processing your bda agent query: {str(e)}"