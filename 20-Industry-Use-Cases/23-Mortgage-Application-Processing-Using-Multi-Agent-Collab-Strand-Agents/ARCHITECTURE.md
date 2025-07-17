# Document Processing System Architecture

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Document      │    │   Processing    │    │   HTTP Webhook  │
│   Upload S3     │───▶│   Lambda        │───▶│   Endpoint      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐
│  OpenSearch     │◀───│   Bedrock KB     │
│  Serverless     │    │   Knowledge Base │
└─────────────────┘    └──────────────────┘
```

## Component Design

### 1. Document Storage (S3)
- **Purpose**: Primary storage for uploaded documents
- **Configuration**:
  - Versioning enabled
  - Server-side encryption (SSE-S3)
  - Public access blocked
  - Direct Lambda trigger on object creation

### 2. Event Processing (Lambda)
- **Purpose**: Process document upload events and call HTTP webhook
- **Trigger**: Direct S3 event notification
- **Flow**:
  1. S3 sends event directly to Lambda
  2. Lambda processes document metadata
  3. Lambda calls HTTP webhook endpoint

### 3. Vector Storage (OpenSearch Serverless)
- **Purpose**: Store document embeddings for retrieval
- **Configuration**:
  - Optimized for frequent access
  - Integration with Bedrock KB

### 4. Knowledge Base (Amazon Bedrock)
- **Purpose**: Enable semantic search and retrieval
- **Configuration**:
  - Connected to OpenSearch Serverless
  - Embedding model: Amazon Titan
  - Data source: Document storage S3

## Security Architecture

### IAM Roles and Policies
- **Lambda Execution Role**: Access to S3, Bedrock
- **Bedrock Service Role**: Access to document S3 and OpenSearch
- **S3 Bucket Policies**: Restrict access to authorized services

### Encryption
- **S3**: Server-side encryption with AWS managed keys
- **Lambda**: Environment variables encrypted
- **OpenSearch**: Encryption at rest and in transit

## Simplified Benefits
- **Reduced Complexity**: No EventBridge configuration needed
- **Lower Latency**: Direct S3 to Lambda trigger
- **Cost Optimization**: Fewer AWS services involved
- **Easier Debugging**: Simpler event flow to troubleshoot

## Terraform Structure

```
terraform/
├── main.tf              # Main configuration
├── variables.tf         # Input variables
├── outputs.tf          # Output values
├── providers.tf        # Provider configuration
├── versions.tf         # Version constraints
├── lambda/
│   └── document_processor.py
└── environments/
    └── dev/
        └── terraform.tfvars
```

## Deployment Strategy
1. **Phase 1**: S3 bucket and IAM roles
2. **Phase 2**: Lambda function with S3 trigger
3. **Phase 3**: Bedrock Knowledge Base integration
4. **Phase 4**: Testing and validation
