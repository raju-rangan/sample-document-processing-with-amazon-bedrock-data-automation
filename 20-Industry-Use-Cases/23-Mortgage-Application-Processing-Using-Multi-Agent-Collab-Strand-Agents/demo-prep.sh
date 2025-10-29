#!/bin/bash

# Demo Preparation Script for Mortgage Application Processing
# Updated: October 22, 2025

set -e

echo "🏠 Mortgage Application Processing Demo - Preparation Script"
echo "=========================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Terraform version
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install Terraform >= 1.13.4"
    exit 1
fi

TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version')
echo "✅ Terraform version: $TERRAFORM_VERSION"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI"
    exit 1
fi

echo "✅ AWS CLI configured for region: $(aws configure get region)"

# Check UV
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Please install UV package manager"
    exit 1
fi

echo "✅ UV version: $(uv --version)"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker"
    exit 1
fi

echo "✅ Docker version: $(docker --version)"

echo ""
echo "🔧 Setting up environment..."

# Install/update dependencies
echo "📦 Installing Python dependencies..."
uv sync

# Activate virtual environment
source .venv/bin/activate

echo "✅ Virtual environment activated"

echo ""
echo "🏗️  Infrastructure deployment..."

# Initialize and apply Terraform
echo "🚀 Deploying infrastructure..."
make terraform-apply

echo ""
echo "📊 Getting infrastructure outputs..."
make terraform-output

echo ""
echo "🤖 Configuring AgentCore..."

# Get IAM role from terraform output
IAM_ROLE=$(cd infrastructure/terraform && terraform output -raw agentcore_iam_role_name)
BDA_BUCKET=$(cd infrastructure/terraform && terraform output -raw bda_s3_bucket_name)

echo "📝 Configuring agent with IAM role: $IAM_ROLE"
agentcore configure --entrypoint main.py -er "$IAM_ROLE"

echo "🚀 Launching agent..."
agentcore launch --env "AWS_BUCKET_NAME=$BDA_BUCKET"

echo ""
echo "✅ Demo preparation complete!"
echo ""
echo "🎯 Next steps for your presentation:"
echo "1. Test the Streamlit UI: streamlit run src/streamlit/app.py"
echo "2. Upload sample documents from the documents/ folder"
echo "3. Monitor processing in CloudWatch logs"
echo "4. Show results in DynamoDB console"
echo ""
echo "📚 Key demo points:"
echo "- Multi-agent collaboration with Bedrock AgentCore"
echo "- Serverless document processing pipeline"
echo "- Real-time UI with Streamlit"
echo "- Observability with OpenTelemetry"
echo ""
echo "🔗 Useful links:"
echo "- S3 Raw Bucket: $(cd infrastructure/terraform && terraform output -raw raw_s3_bucket_name)"
echo "- S3 BDA Bucket: $BDA_BUCKET"
echo "- DynamoDB Table: mortgage-applications"
echo ""
echo "Happy presenting! 🎉"
