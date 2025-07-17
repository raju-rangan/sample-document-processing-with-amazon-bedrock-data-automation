# Document Processing System with Amazon Bedrock

A comprehensive document processing system built with Terraform that automatically processes uploaded documents, triggers webhooks, and enables semantic search through Amazon Bedrock Knowledge Base.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Document      │    │   EventBridge    │    │   Processing    │
│   Upload S3     │───▶│   Rule           │───▶│   Lambda        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  OpenSearch     │◀───│   Bedrock KB     │◀───│   HTTP Webhook  │
│  Serverless     │    │   Knowledge Base │    │   Endpoint      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Features

- **Automated Document Processing**: Automatically processes documents uploaded to S3
- **Event-Driven Architecture**: Uses EventBridge for reliable event processing
- **HTTP Webhook Integration**: Triggers HTTP requests with document metadata
- **Semantic Search**: Bedrock Knowledge Base for intelligent document retrieval
- **Vector Storage**: OpenSearch Serverless for scalable vector operations
- **Security First**: IAM roles with least privilege, encryption at rest
- **Cost Optimized**: S3 lifecycle policies and serverless architecture
- **Multi-Environment**: Separate configurations for dev/prod environments

## 📋 Components

### Core Infrastructure
- **S3 Buckets**: Document storage with versioning and encryption
- **EventBridge**: Event routing for S3 object creation
- **Lambda Function**: Document processing and webhook integration
- **IAM Roles**: Secure access control with least privilege

### AI/ML Components
- **Amazon Bedrock Knowledge Base**: Semantic search and retrieval
- **OpenSearch Serverless**: Vector storage and indexing
- **Titan Embedding Model**: Document vectorization

## 🛠️ Prerequisites

- Terraform >= 1.6.0
- AWS CLI configured
- Access to Amazon Bedrock service
- Appropriate AWS permissions (see [DEPLOYMENT.md](./DEPLOYMENT.md))

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Configure webhook URL**
   ```bash
   vim terraform/environments/dev/terraform.tfvars
   # Update webhook_url to your endpoint
   ```

3. **Deploy infrastructure**
   ```bash
   make init
   make plan
   make apply
   ```

4. **Test the system**
   ```bash
   make test
   make logs
   ```

## 🔧 Available Commands

- `make init` - Initialize Terraform
- `make plan` - Plan deployment
- `make apply` - Deploy infrastructure
- `make destroy` - Destroy infrastructure
- `make test` - Upload test document
- `make logs` - Show Lambda logs
- `make clean` - Clean temporary files

## 📁 Project Structure

```
├── REQUIREMENTS.md          # System requirements and acceptance criteria
├── ARCHITECTURE.md          # Detailed architecture documentation
├── DEPLOYMENT.md           # Comprehensive deployment guide
├── README.md              # This file
├── terraform/
│   ├── main.tf            # Main Terraform configuration
│   ├── variables.tf       # Input variables with validation
│   ├── outputs.tf         # Output values
│   ├── providers.tf       # Provider configuration
│   ├── versions.tf        # Version constraints
│   ├── lambda/
│   │   └── document_processor.py  # Lambda function code
│   └── environments/
│       ├── dev/
│       │   └── terraform.tfvars   # Development configuration
│       └── prod/
│           └── terraform.tfvars   # Production configuration
└── documents/             # Sample documents for testing
```

## 🔧 Configuration

### Environment Variables
Key configuration options in `terraform.tfvars`:

```hcl
# Project Settings
project_name = "document-processing"
environment  = "dev"
aws_region   = "us-east-1"

# Webhook Configuration
webhook_url = "https://your-webhook-endpoint.com/webhook"

# Bedrock Configuration
bedrock_model_arn = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
```

### Webhook Payload
The system sends HTTP POST requests with the following payload:

```json
{
  "event_type": "document_uploaded",
  "timestamp": "2025-07-17T20:00:00Z",
  "document": {
    "bucket": "document-processing-dev-document-storage-abc123",
    "key": "document.pdf",
    "size": 1024,
    "content_type": "application/pdf",
    "last_modified": "2025-07-17T20:00:00Z"
  },
  "s3_event": {
    "event_name": "ObjectCreated:Put",
    "source": "aws.s3"
  },
  "processing": {
    "vector_bucket": "document-processing-dev-vector-storage-abc123",
    "status": "initiated"
  }
}
```

## 🔍 Monitoring

### CloudWatch Logs
- Lambda function logs: `/aws/lambda/{function-name}`
- Retention period: 14 days
- Log level: INFO with detailed error handling

### Key Metrics to Monitor
- Lambda function duration and errors
- S3 bucket size and request metrics
- EventBridge rule invocations
- OpenSearch Serverless capacity units

## 💰 Cost Optimization

- **S3 Lifecycle Policies**: Automatic transition to cheaper storage classes
- **Serverless Architecture**: Pay only for what you use
- **Resource Tagging**: Comprehensive cost tracking
- **Right-Sized Resources**: Optimized for small to medium scale

## 🔒 Security

- **Encryption**: Server-side encryption on all S3 buckets
- **IAM**: Least privilege access with specific resource ARNs
- **Network Security**: Public access blocked on S3 buckets
- **Access Policies**: Fine-grained OpenSearch Serverless access control

## 🧪 Testing

### Unit Testing
```bash
# Test Lambda function locally
python terraform/lambda/document_processor.py
```

### Integration Testing
```bash
# Upload test document and verify webhook
./scripts/test-integration.sh
```

### Load Testing
```bash
# Upload multiple documents simultaneously
./scripts/load-test.sh
```

## 📚 Documentation

- [System Requirements](./REQUIREMENTS.md) - Functional and non-functional requirements
- [Architecture Design](./ARCHITECTURE.md) - Detailed system architecture
- [Deployment Guide](./DEPLOYMENT.md) - Step-by-step deployment instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the MBSE principles
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the [Troubleshooting section](./DEPLOYMENT.md#troubleshooting) in the deployment guide
2. Review CloudWatch logs for error details
3. Open an issue with detailed error information

## 🔄 Changelog

- **v1.0.0** - Initial release with core functionality
- **v1.1.0** - Added Bedrock Knowledge Base integration
- **v1.2.0** - Enhanced security and monitoring features
