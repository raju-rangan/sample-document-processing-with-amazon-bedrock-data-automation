from strands import Agent, tool
from strands import Agent
from strands.tools.mcp import MCPClient
import boto3
from strands.models import BedrockModel
from mcp import stdio_client, StdioServerParameters
import os

DATA_EXTRACTION_SYSTEM_PROMPT = """
<context>
You are a specialized data extraction agent for the "mortgage-application-processing" Bedrock Data Automation project. You analyze mortgage documents and extract data for storage in DynamoDB (structured) and S3 (unstructured).
</context>

<instructions>
1. Extract all relevant data from mortgage applications, loan documents, financial statements, and supporting materials
2. Categorize data as structured (for DynamoDB) or unstructured (for S3)
3. Validate all extracted information and assign confidence scores
4. Flag incomplete or suspicious data for human review
5. Return only valid JSON output
</instructions>

<output_format>
```json
{
  "structured_data": {
    ...
  },
  "unstructured_data": {
    "document_type": "string",
    "extracted_text": "string",
    "confidence_score": "number",
    "requires_review": "boolean",
    "notes": "string"
  },
  "storage_routing": {
    "dynamodb_items": ["structured_data"],
    "s3_items": ["unstructured_data", "original_document"]
  }
}
```
</output_format>

<validation_rules>
- Extract numerical values as numbers, not strings
- Verify SSN format: XXX-XX-XXXX
- Validate positive loan amounts
- Use date format: YYYY-MM-DD
- Assign confidence scores (0.0-1.0)
- Set requires_review: true for unclear/incomplete data
</validation_rules>
"""

session = boto3.Session(
    region_name=os.environ.get('AWS_REGION','us-east-1'),
)

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    boto_session=session,
)

bda_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-bedrock-data-automation-mcp-server@latest"],
        env={
            'AWS_REGION': os.environ.get('AWS_REGION', 'us-east-1'),
            'AWS_BUCKET_NAME': os.environ.get('AWS_BUCKET_NAME', ''),
            'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID', ''),
            'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
            'AWS_SESSION_TOKEN': os.environ.get('AWS_SESSION_TOKEN', ''),
            "UV_CONSTRAINT": "requirements.txt"
        }
    )
))

bda_mcp_client.start()

data_extraction_agent = Agent( 
    name="data_extraction_agent",
    system_prompt=DATA_EXTRACTION_SYSTEM_PROMPT,
    model=bedrock_model,
    tools=bda_mcp_client.list_tools_sync(),
)