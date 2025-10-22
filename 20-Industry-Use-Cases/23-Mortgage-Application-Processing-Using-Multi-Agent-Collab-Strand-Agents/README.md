# Mortgage Application Processing with Multi-Agent Collaboration

![architecture](./assets/arch.drawio.png)

## Overview
This demo showcases an intelligent mortgage application processing system using Amazon Bedrock's multi-agent collaboration capabilities. The system automatically processes mortgage documents, extracts key information, and provides structured analysis through a collaborative agent workflow.

## Architecture Components
- **Amazon Bedrock AgentCore**: Orchestrates multi-agent workflows
- **S3 Buckets**: Raw document storage and processed data storage
- **Lambda Functions**: Document preprocessing and CRUD operations
- **DynamoDB**: Application data storage

## Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform >= 1.13.4
- Python >= 3.13
- Docker (for containerized deployment)
- UV package manager

## Getting Started

### 1. Deploy Infrastructure

```sh
make terraform-apply
```

Expected output:
```
agentcore_ecr_repository_url = "************.dkr.ecr.us-east-1.amazonaws.com/bedrock_agentcore-dev"
agentcore_iam_role_name = "agentcore-dev-iam-role"
bda_s3_bucket_name = "bedrock-data-automation-store**************"
mortgage_api_url = "https://************.us-east-1.amazonaws.com"
mortgage_crud_function_name = "mortgage-applications-crud"
mortgage_preprocessor_function_name = "mortgage-preprocess"
raw_s3_bucket_name = "raw-document-store**************"
```

### 2. Deploy Agent via AgentCore

Configure the agent using the IAM role from terraform output:

```sh
agentcore configure --entrypoint main.py -er agentcore-dev-iam-role
```

Launch to AWS:
```sh
agentcore launch
```

### 3. Test the System

Upload a mortgage application PDF through the Streamlit interface or directly to the S3 bucket to trigger the processing workflow.

## Local Development

### Setup Environment
```sh
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

### Environment Variables
- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_BUCKET_NAME`: S3 bucket for processed documents
- `LOGGING_LEVEL`: Application logging level
```
