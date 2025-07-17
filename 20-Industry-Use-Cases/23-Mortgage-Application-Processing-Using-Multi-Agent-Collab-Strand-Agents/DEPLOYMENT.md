# Document Processing System - Deployment Guide

## Prerequisites

- Terraform >= 1.6.0
- AWS CLI configured
- Access to Amazon Bedrock service

## Quick Start

1. **Configure webhook URL**
   ```bash
   vim terraform/environments/dev/terraform.tfvars
   # Update webhook_url to your endpoint
   ```

2. **Deploy**
   ```bash
   make init
   make plan
   make apply
   ```

3. **Test**
   ```bash
   make test
   make logs
   ```

## Available Commands

- `make init` - Initialize Terraform
- `make plan` - Plan deployment
- `make apply` - Deploy infrastructure
- `make destroy` - Destroy infrastructure
- `make test` - Upload test document
- `make logs` - Show Lambda logs
- `make clean` - Clean temporary files

## Configuration

Edit `terraform/environments/dev/terraform.tfvars`:

```hcl
webhook_url = "https://your-webhook-endpoint.com/webhook"
```

## Testing

After deployment:
1. Run `make test` to upload a test document
2. Run `make logs` to see processing logs
3. Check your webhook endpoint for the payload

## Cleanup

```bash
make destroy
```
