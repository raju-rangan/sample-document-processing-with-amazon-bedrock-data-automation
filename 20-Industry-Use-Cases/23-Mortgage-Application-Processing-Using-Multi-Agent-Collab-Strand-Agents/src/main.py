from strands import Agent
from bda_agent_assistant import bda_agent_assistant
from dynamo_agent_assistant import dynamo_agent_assistant
from kb_retrieval_assistant import kb_retrieval_assistant
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import uvicorn
import os


app = FastAPI(title="Mortgage Process API")

SYSTEM_PROMPT = """
"""


class PromptRequest(BaseModel):
    prompt: str

@app.get('/health')
def health_check():
    """Health check endpoint for the load balancer."""
    return {"status": "healthy"}


@app.post('/process_mortgage')
async def get_arithmetic(request: PromptRequest):
    prompt = request.prompt
    
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")

    try:
        tools = [bda_agent_assistant,dynamo_agent_assistant,kb_retrieval_assistant]
        agent = Agent(tools=tools,
                    callback_handler=None)
        response = agent(prompt)

        content = str(response)
        return PlainTextResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8001))
    uvicorn.run(app, host='0.0.0.0', port=port)