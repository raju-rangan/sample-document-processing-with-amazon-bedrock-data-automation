# Document Processing System - Deployment Guide

## Prerequisites

### Required Tools
- Terraform >= 1.6.0
- AWS CLI configured with appropriate credentials
- Access to AWS Bedrock service in your region

### AWS Permissions Required
- S3: Full access for bucket creation and management
- IAM: Role and policy creation
- Lambda: Function creation and management
- EventBridge: Rule creation and management
- Bedrock: Knowledge Base and data source management
- OpenSearch Serverless: Collection and policy management
- CloudWatch: Log group creation

## Deployment Steps

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd terraform/
```

### 2. Initialize Terraform
```bash
terraform init
```

### 3. Plan Deployment (Development)
```bash
terraform plan -var-file="environments/dev/terraform.tfvars"
```

### 4. Deploy Infrastructure
```bash
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### 5. Verify Deployment
```bash
# Check S3 buckets
aws s3 ls | grep document-processing

# Check Lambda function
aws lambda list-functions --query 'Functions[?contains(FunctionName, `document-processing`)]'

# Check EventBridge rules
aws events list-rules --name-prefix document-processing

# Check Bedrock Knowledge Base
aws bedrock-agent list-knowledge-bases
```

## Environment-Specific Deployments

### Development Environment
```bash
terraform workspace new dev
terraform plan -var-file="environments/dev/terraform.tfvars"
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### Production Environment
```bash
terraform workspace new prod
terraform plan -var-file="environments/prod/terraform.tfvars"
terraform apply -var-file="environments/prod/terraform.tfvars"
```

## Configuration

### Webhook URL Configuration
1. Update the `webhook_url` variable in your environment's `terraform.tfvars`
2. For testing, you can use https://webhook.site to create a temporary endpoint
3. For production, use your actual webhook endpoint

### Bedrock Model Configuration
- Default: Amazon Titan Embed Text v1
- Ensure the model is available in your AWS region
- Update `bedrock_model_arn` if using a different model

## Testing the System

### 1. Upload a Test Document
```bash
# Get bucket name from Terraform output
BUCKET_NAME=$(terraform output -raw document_bucket_name)

# Upload a test file
aws s3 cp test-document.pdf s3://$BUCKET_NAME/
```

### 2. Check Lambda Logs
```bash
# Get function name
FUNCTION_NAME=$(terraform output -raw lambda_function_name)

# View logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/$FUNCTION_NAME"
```

### 3. Verify Webhook Call
- Check your webhook endpoint for incoming requests
- Verify the payload structure matches expectations

### 4. Test Knowledge Base
```bash
# Get Knowledge Base ID
KB_ID=$(terraform output -raw knowledge_base_id)

# Test query (requires additional setup)
aws bedrock-agent-runtime retrieve --knowledge-base-id $KB_ID --retrieval-query "test query"
```

## Monitoring and Maintenance

### CloudWatch Logs
- Lambda function logs: `/aws/lambda/{function-name}`
- Retention: 14 days (configurable)

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

1. **Bedrock Model Not Available**
   - Ensure the model is available in your region
   - Check if you have access to Bedrock service

2. **Lambda Function Timeout**
   - Check CloudWatch logs for errors
   - Verify webhook URL is accessible
   - Increase timeout if needed

3. **EventBridge Not Triggering**
   - Verify S3 bucket notification is enabled
   - Check EventBridge rule pattern matches S3 events

4. **OpenSearch Serverless Access Issues**
   - Verify security policies are correctly configured
   - Check IAM role permissions

### Cleanup
```bash
# Destroy all resources
terraform destroy -var-file="environments/dev/terraform.tfvars"

# Or for specific workspace
terraform workspace select dev
terraform destroy -var-file="environments/dev/terraform.tfvars"
```

## Support and Maintenance

### Regular Tasks
- Monitor CloudWatch logs for errors
- Review S3 storage costs and lifecycle policies
- Update Lambda function code as needed
- Rotate IAM credentials regularly

### Scaling Considerations
- Lambda concurrency limits
- S3 request rate limits
- OpenSearch Serverless capacity units
- EventBridge rule limits
