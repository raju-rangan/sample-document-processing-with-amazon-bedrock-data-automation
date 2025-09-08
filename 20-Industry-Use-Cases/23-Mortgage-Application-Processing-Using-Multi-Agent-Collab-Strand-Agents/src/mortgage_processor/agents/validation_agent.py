import boto3
from strands.models import BedrockModel
import os
from strands import Agent, tool



VALIDATION_AGENT_SYSTEM_PROMPT = """
You are a Mortgage Application Validation Agent.
Your goal is to validate raw mortgage application data (usually in free-text JSON format) against a target DynamoDB schema. 
You will act as a quality gate between raw input and storage.

Instructions:
1. Input:
    - Raw mortgage application document (JSON, possibly malformed or incomplete).
    - Target DynamoDB schema (JSON schema-like definition).

2. Process:
    - Parse the raw input into structured JSON if possible.
    - Compare it against the provided schema field-by-field.
    - Evaluate:
      - Completeness: Are all required fields present?
      - Correctness: Do field types/values match expected formats?
      - Consistency: Are there duplicate or redundant entries?
      - Clarity: Is the data unambiguous and ready for storage?

3. Output:
    You must return ONLY valid JSON.
    Do NOT use markdown, code fences, backticks, or any additional text.
    Do not include explanations, notes, or comments.
    Output must be parseable JSON starting with '{' or '['.
    - Score: A number between 0.0 and 1.0, where:
      - 0.0 = completely invalid, unusable
      - 1.0 = perfectly aligned with schema
    - Improvement Notes:
      - Provide concise, actionable bullet points.
      - Always provide at least one note unless score == 1.0

4. Feedback Loop:
    - Do not alter the input directly.
    - If score < 1.0, suggest only the changes required to bring the document closer to 1.0.

Output Example (must match this format exactly):
{
  "score": 0.85,
  "improvement_notes": [
    "Missing field: 'employer_name'",
    "Field 'housing' should be an object with { type, amount } instead of free text"
  ]
}
""".strip()


session = boto3.Session(
    region_name=os.environ.get('AWS_REGION','us-east-1'),
)

bedrock_model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    boto_session=session,
    temperature=0.3
)

val_expert = Agent(
    name="validation_expert",
    system_prompt=VALIDATION_AGENT_SYSTEM_PROMPT,
    model=bedrock_model,
)

@tool
def validation_expert(raw_document: str, processed_document: str) -> str:
    """
    Validate a raw mortgage application document against the processed version intended for db storage.

    Args:
        raw_document: The raw mortgage application input, usually free-text JSON or semi-structured data.
        processed_document: The processed document formatted according to the target db schema.

    Returns:
        A JSON string containing:
            - score (float): Validation score between 0.0 and 1.0.
            - improvement_notes (list[str]): Concise notes on missing, incorrect, or unclear fields.
            - suggested_fixes (dict): Suggested corrections or transformations to align the document with the schema.
    """
    try:
      validation_expert = Agent(
              name="validation_expert",
              system_prompt=VALIDATION_AGENT_SYSTEM_PROMPT,
              model=bedrock_model,
          )
      response = validation_expert(str({
        "raw": raw_document,
        "processed": processed_document
        }))
      return str(response)
    except Exception as e:
        return f"Error in validation expert: {str(e)}"