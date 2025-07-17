# Document Processing System - Deployment Guide

## Prerequisites

### Required Tools
- Terraform >= 1.6.0
- AWS CLI configured with appropriate credentials
- Access to AWS Bedrock service in your region
- Make utility (usually pre-installed on Linux/macOS)

### AWS Permissions Required
- S3: Full access for bucket creation and management
- IAM: Role and policy creation
- Lambda: Function creation and management
- EventBridge: Rule creation and management
- Bedrock: Knowledge Base and data source management
- OpenSearch Serverless: Collection and policy management
- CloudWatch: Log group creation

## Quick Start with Makefile

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd <project-directory>
```

### 2. View Available Commands
```bash
make help
```

### 3. Deploy Development Environment
```bash
# Complete development deployment
make dev

# Or step by step:
make dev-init    # Initialize Terraform
make dev-plan    # Plan deployment
make dev-apply   # Apply configuration
```

### 4. Deploy Production Environment
```bash
make prod-init
make prod-plan
make prod-apply
```

## Available Make Commands

### Core Commands
- `make help` - Show all available commands
- `make init ENV=<dev|prod>` - Initialize Terraform
- `make plan ENV=<dev|prod>` - Plan deployment
- `make apply ENV=<dev|prod>` - Apply configuration
- `make destroy ENV=<dev|prod>` - Destroy infrastructure

### Development Shortcuts
- `make dev` - Complete dev deployment (init + plan + apply)
- `make dev-init` - Initialize development environment
- `make dev-plan` - Plan development deployment
- `make dev-apply` - Apply development configuration
- `make dev-destroy` - Destroy development infrastructure

### Production Shortcuts
- `make prod-init` - Initialize production environment
- `make prod-plan` - Plan production deployment
- `make prod-apply` - Apply production configuration
- `make prod-destroy` - Destroy production infrastructure

### Utility Commands
- `make validate` - Validate Terraform configuration
- `make format` - Format Terraform files
- `make output ENV=<dev|prod>` - Show Terraform outputs
- `make status ENV=<dev|prod>` - Show infrastructure status
- `make clean` - Clean temporary files

### Testing Commands
- `make test-upload ENV=<dev|prod>` - Upload test document
- `make logs ENV=<dev|prod>` - Show Lambda function logs
- `make test ENV=<dev|prod>` - Run integration test

## Configuration

### Webhook URL Configuration
1. Edit the webhook URL in your environment's terraform.tfvars:
   ```bash
   # For development
   vim terraform/environments/dev/terraform.tfvars
   
   # For production
   vim terraform/environments/prod/terraform.tfvars
   ```

2. Update the `webhook_url` variable:
   ```hcl
   webhook_url = "https://your-webhook-endpoint.com/webhook"
   ```

### Bedrock Model Configuration
- Default: Amazon Titan Embed Text v1
- Ensure the model is available in your AWS region
- Update `bedrock_model_arn` if using a different model

## Testing the System

### 1. Upload a Test Document
```bash
make test-upload ENV=dev
```

### 2. Check Lambda Logs
```bash
make logs ENV=dev
```

### 3. View Infrastructure Status
```bash
make status ENV=dev
```

### 4. Manual Testing
```bash
# Get bucket name and upload custom file
BUCKET_NAME=$(cd terraform && terraform output -raw document_bucket_name)
aws s3 cp your-document.pdf s3://$BUCKET_NAME/
```

## Environment Management

### Development Environment
```bash
# Deploy development
make dev

# Check status
make status ENV=dev

# Test the system
make test ENV=dev

# Clean up
make dev-destroy
```

### Production Environment
```bash
# Deploy production
make prod-init
make prod-plan
make prod-apply

# Monitor
make logs ENV=prod
make status ENV=prod
```

## Monitoring and Maintenance

### CloudWatch Logs
```bash
# Follow logs in real-time
make logs ENV=dev

# Or manually
aws logs tail "/aws/lambda/$(cd terraform && terraform output -raw lambda_function_name)" --follow
```

### Cost Optimization
- S3 lifecycle policies automatically transition objects to cheaper storage classes
- OpenSearch Serverless scales automatically
- Lambda charges only for execution time

### Security Best Practices
- All S3 buckets have public access blocked
- IAM roles follow least privilege principle
- Server-side encryption enabled on all storage

## Troubleshooting

### Common Issues

1. **Terraform Initialization Fails**
   ```bash
   make clean
   make init ENV=dev
   ```

2. **AWS Credentials Issues**
   ```bash
   aws configure list
   aws sts get-caller-identity
   ```

3. **Bedrock Model Not Available**
   - Ensure the model is available in your region
   - Check if you have access to Bedrock service

4. **Lambda Function Timeout**
   ```bash
   make logs ENV=dev
   ```

5. **EventBridge Not Triggering**
   - Verify S3 bucket notification is enabled
   - Check EventBridge rule pattern matches S3 events

### Cleanup
```bash
# Destroy specific environment
make destroy ENV=dev

# Clean temporary files
make clean
```

## Advanced Usage

### Custom Environment Variables
```bash
# Use custom variable file
cd terraform
terraform plan -var-file="custom.tfvars"
```

### Terraform State Management
```bash
# Show current state
cd terraform && terraform show

# Import existing resources
cd terraform && terraform import aws_s3_bucket.example bucket-name
```

### Multiple Environments
```bash
# Deploy both environments
make dev
make prod

# Compare configurations
make plan ENV=dev
make plan ENV=prod
```

## Support and Maintenance

### Regular Tasks
- Monitor CloudWatch logs for errors: `make logs ENV=<env>`
- Review S3 storage costs and lifecycle policies
- Update Lambda function code as needed
- Rotate IAM credentials regularly

### Scaling Considerations
- Lambda concurrency limits
- S3 request rate limits
- OpenSearch Serverless capacity units
- EventBridge rule limits

### Backup and Recovery
```bash
# Export Terraform state
cd terraform && terraform show > infrastructure-backup.txt

# List all resources
cd terraform && terraform state list
```
