# Mortgage Application Processing with Multi-Agent Collaboration

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Terraform](https://img.shields.io/badge/terraform-1.13.4+-purple.svg)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![Strands](https://img.shields.io/badge/Strands-Agents-green.svg)](https://github.com/aws-samples/strands-agents)

## What This Does

This system transforms manual mortgage application processing into an automated, intelligent workflow. Upload a mortgage document to S3, and watch as multiple AI agents collaborate to extract, process, and store structured data automatically.

## Architecture

![System Architecture](./assets/arch.drawio.png)

## Quick Start

### 1. Setup Environment

```bash
git clone <repository-url>
cd mortgage-processing-system
uv sync
source .venv/bin/activate
```

### 2. Deploy Infrastructure

```bash
make terraform-apply
```

This creates:
- S3 buckets for raw documents and processed data
- DynamoDB table for application storage
- Lambda functions for preprocessing and CRUD operations
- IAM roles and policies
- API Gateway endpoints

### 3. Deploy AgentCore Gateway

```bash
make create-gateway
```

### 4. Configure and Deploy Agents

```bash
# Configure AgentCore with the created IAM role
make agent-configure

# Deploy AgentCore to AWS
make agent-launch
```

### 4. Upload Documents for Processing

```bash
# Upload sample documents to trigger processing
make upload-docs
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for resources | `us-east-1` |
| `AWS_BUCKET_NAME` | S3 bucket for processed documents | From Terraform |
| `LOGGING_LEVEL` | Application logging level | `INFO` |
| `EXTRACTION_AGENT_MODEL_ID` | Bedrock model for extraction | `global.anthropic.claude-sonnet-4-20250514-v1:0` |
| `STORAGE_AGENT_MODEL_ID` | Bedrock model for storage | `global.anthropic.claude-sonnet-4-20250514-v1:0` |

## Local Deployment

```bash
# Test agents locally
make agent-launch  # Uses --local flag for local execution

# Update dependencies
make update-deps

# Create MCP gateway
make create-gateway
```