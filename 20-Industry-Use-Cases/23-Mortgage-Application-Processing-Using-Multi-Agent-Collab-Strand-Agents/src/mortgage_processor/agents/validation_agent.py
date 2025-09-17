import boto3
from strands.models import BedrockModel
import os
from strands import Agent, tool



VALIDATION_AGENT_SYSTEM_PROMPT = """
You are a Mortgage Application Validation Agent.
Your goal is to validate raw mortgage application data against a target schema. 

Instructions:
1. Input:
    - JSON mortgage application document.

2. Process:
    - Evaluate against this perfect mortgage application:

{
  "assets": {
    "accounts": []
  },
  "borrower_name": "John Doe",
  "declarations": [],
  "employment_history": [
    {
      "address": "456 Tech Avenue, San Francisco, CA, 94102, USA",
      "employer": "Acme Corp",
      "monthly_base_income": 7500,
      "position": "Senior Software Engineer",
      "start_date": "2019-08-15"
    }
  ],
  "liabilities": [],
  "loan_amount": 350000,
  "loan_information": {
    "occupancy": "Primary Residence",
    "property": {
      "address": "456 Maple Lane, CityVille, NY, 12345",
      "value": 550000
    },
    "purpose": "Purchase"
  },
  "personal_information": {
    "citizenship": "U.S. Citizen",
    "contact": {
      "address": "123 Main St, Reston, VA 20170, USA",
      "cell_phone": "555-987-4567",
      "email": "john.doe@example.com",
      "housing_payment": 2200,
      "housing_situation": "Renting"
    },
    "credit_type": "Individual application",
    "date_of_birth": "1970-09-21",
    "dependents": 2,
    "marital_status": "Single"
  },
  "ssn": "123-45-6789",
  "status": "pending",
  "underwriter_notes": [
    "No payment shock expected based on current rent vs projected mortgage",
    "supports creditworthiness",
    "Diverse asset mix shows financial responsibility",
    "strengthens application",
    "tech"
  ],
}

3. Output:
    - Score: A number between 0.0 and 1.0, where:
      - 0.0 = completely invalid, unusable
      - 1.0 = perfectly aligned with schema
    - Feedback:
      - Provide concise, actionable bullet points.
""".strip()


session = boto3.Session(
    region_name=os.environ.get('AWS_REGION','us-east-1'),
)

bedrock_model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    boto_session=session,
    temperature=0.0
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