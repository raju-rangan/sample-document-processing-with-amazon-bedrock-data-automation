# Document Processing System Architecture

## High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Document      │    │   EventBridge    │    │   Processing    │
│   Upload S3     │───▶│   Rule           │───▶│   Lambda        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Vector Store  │◀───│   Bedrock KB     │◀───│   HTTP Webhook  │
│   S3 Bucket     │    │   Knowledge Base │    │   Endpoint      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Component Design

### 1. Document Storage (S3)
- **Purpose**: Primary storage for uploaded documents
- **Configuration**:
  - Versioning enabled
  - Server-side encryption (SSE-S3)
  - Public access blocked
  - Event notifications enabled

### 2. Event Processing (EventBridge + Lambda)
- **Purpose**: Process document upload events
- **Flow**:
  1. S3 sends event to EventBridge
  2. EventBridge rule triggers Lambda
  3. Lambda processes document and calls HTTP endpoint

### 3. Vector Storage (S3)
- **Purpose**: Store document embeddings for retrieval
- **Configuration**:
  - Optimized for frequent access
  - Integration with Bedrock KB

### 4. Knowledge Base (Amazon Bedrock)
- **Purpose**: Enable semantic search and retrieval
- **Configuration**:
  - Connected to vector store S3
  - Embedding model: Amazon Titan
  - Chunking strategy configured

## Security Architecture

### IAM Roles and Policies
- **Lambda Execution Role**: Access to S3, EventBridge, Bedrock
- **Bedrock Service Role**: Access to vector store S3
- **S3 Bucket Policies**: Restrict access to authorized services

### Encryption
- **S3**: Server-side encryption with AWS managed keys
- **EventBridge**: Encryption in transit
- **Lambda**: Environment variables encrypted

## Terraform Module Structure

```
terraform/
├── main.tf              # Main configuration
├── variables.tf         # Input variables
├── outputs.tf          # Output values
├── providers.tf        # Provider configuration
├── versions.tf         # Version constraints
├── modules/
│   ├── s3/             # S3 bucket module
│   ├── eventbridge/    # EventBridge module
│   ├── lambda/         # Lambda function module
│   └── bedrock/        # Bedrock KB module
└── environments/
    ├── dev/            # Development environment
    └── prod/           # Production environment
```

## Deployment Strategy
1. **Phase 1**: Core S3 buckets and IAM roles
2. **Phase 2**: EventBridge and Lambda function
3. **Phase 3**: Bedrock Knowledge Base integration
4. **Phase 4**: Testing and validation
