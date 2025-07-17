from strands import Agent, tool
from strands import Agent
from strands.tools.mcp import MCPClient
import boto3
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters


DYNAMODB_AGENT_ASSISTANT_SYSTEM_PROMPT = """

"""


@tool
def dynamo_agent_assistant(query: str) -> str:
    """
    Process DynamoDB requests.
    
    Args:
        query: The user's DynamoDB request
        
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

    dynamo_mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="uvx", 
            args=["awslabs.dynamodb-mcp-server@latest"]
        )
    ))

    # Format the query for the agent with clear instructions
    formatted_query = f"Address this dynamodb request: {query}"
    
    try:
        print("Routed to DynamoDB Agent Assistant")
        # Create the agent with relevant tools
        dynamodb_agent = Agent(
            system_prompt=DYNAMODB_AGENT_ASSISTANT_SYSTEM_PROMPT,
            model=bedrock_model,
            tools=dynamo_mcp_client.list_tools_sync(),
        )
        agent_response = dynamodb_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response
        
        return "I apologize, but I couldn't process your dynamodb request."
    except Exception as e:
        return f"Error processing your dynamodb agent query: {str(e)}"