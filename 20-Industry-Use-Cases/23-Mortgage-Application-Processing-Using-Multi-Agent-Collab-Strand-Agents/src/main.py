from strands import Agent
from bda_agent_assistant import bda_agent_assistant
from dynamo_agent_assistant import dynamo_agent_assistant
from kb_retrieval_assistant import kb_retrieval_assistant
from bedrock_agentcore.runtime import BedrockAgentCoreApp


app = BedrockAgentCoreApp(debug=True)

SYSTEM_PROMPT = """
You are a mortgage application processor coordinator
"""

tools = [bda_agent_assistant,dynamo_agent_assistant,kb_retrieval_assistant]
agent = Agent(tools=tools,
            system_prompt=SYSTEM_PROMPT,
            callback_handler=None)

@app.entrypoint
async def get_arithmetic(payload):
    user_message = payload.get(
        "prompt", "No prompt found in input, please guide customer to create a json payload with prompt key"
    )

    result = agent(user_message)

    return { "result": result.message }
    
if __name__ == '__main__':
    app.run()