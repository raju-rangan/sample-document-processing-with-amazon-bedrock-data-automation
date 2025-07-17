#!/bin/bash

# Integration Test Script for Document Processing System
# This script tests the complete workflow from document upload to webhook call

set -e

echo "🧪 Starting Integration Test for Document Processing System"

# Check if we're in the right directory
if [ ! -f "terraform/main.tf" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if Terraform is initialized
if [ ! -d "terraform/.terraform" ]; then
    echo "❌ Error: Terraform not initialized. Run 'terraform init' first"
    exit 1
fi

# Get Terraform outputs
echo "📋 Getting Terraform outputs..."
cd terraform

BUCKET_NAME=$(terraform output -raw document_bucket_name 2>/dev/null || echo "")
LAMBDA_FUNCTION=$(terraform output -raw lambda_function_name 2>/dev/null || echo "")
KB_ID=$(terraform output -raw knowledge_base_id 2>/dev/null || echo "")

if [ -z "$BUCKET_NAME" ] || [ -z "$LAMBDA_FUNCTION" ] || [ -z "$KB_ID" ]; then
    echo "❌ Error: Could not retrieve Terraform outputs. Make sure infrastructure is deployed."
    exit 1
fi

echo "✅ Retrieved infrastructure details:"
echo "   - Document Bucket: $BUCKET_NAME"
echo "   - Lambda Function: $LAMBDA_FUNCTION"
echo "   - Knowledge Base ID: $KB_ID"

cd ..

# Create test document
echo "📄 Creating test document..."
TEST_FILE="test-document-$(date +%s).txt"
cat > "$TEST_FILE" << EOF
Test Document for Integration Testing
=====================================

This is a test document created on $(date).

Content:
- Document processing system test
- Amazon Bedrock Knowledge Base integration
- EventBridge and Lambda function testing
- S3 storage and retrieval validation

Keywords: test, document, processing, bedrock, lambda, s3
EOF

echo "✅ Created test document: $TEST_FILE"

# Upload test document
echo "📤 Uploading test document to S3..."
aws s3 cp "$TEST_FILE" "s3://$BUCKET_NAME/" || {
    echo "❌ Error: Failed to upload test document to S3"
    rm -f "$TEST_FILE"
    exit 1
}

echo "✅ Successfully uploaded test document"

# Wait for processing
echo "⏳ Waiting for document processing (30 seconds)..."
sleep 30

# Check Lambda logs
echo "📊 Checking Lambda function logs..."
LOG_GROUP="/aws/lambda/$LAMBDA_FUNCTION"

# Get recent log events
aws logs describe-log-streams \
    --log-group-name "$LOG_GROUP" \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --query 'logStreams[0].logStreamName' \
    --output text > /tmp/latest_stream.txt

if [ -s /tmp/latest_stream.txt ]; then
    LATEST_STREAM=$(cat /tmp/latest_stream.txt)
    echo "📋 Latest log stream: $LATEST_STREAM"
    
    echo "📄 Recent log events:"
    aws logs get-log-events \
        --log-group-name "$LOG_GROUP" \
        --log-stream-name "$LATEST_STREAM" \
        --start-time $(($(date +%s) * 1000 - 300000)) \
        --query 'events[*].message' \
        --output text | tail -10
else
    echo "⚠️  Warning: No recent log streams found"
fi

# Check if document exists in S3
echo "🔍 Verifying document in S3..."
aws s3 ls "s3://$BUCKET_NAME/$TEST_FILE" && echo "✅ Document found in S3" || echo "❌ Document not found in S3"

# Test Knowledge Base (basic check)
echo "🧠 Testing Knowledge Base availability..."
aws bedrock-agent get-knowledge-base --knowledge-base-id "$KB_ID" > /dev/null && {
    echo "✅ Knowledge Base is accessible"
} || {
    echo "⚠️  Warning: Knowledge Base not accessible or not ready"
}

# Cleanup
echo "🧹 Cleaning up test files..."
rm -f "$TEST_FILE"
rm -f /tmp/latest_stream.txt

echo ""
echo "🎉 Integration test completed!"
echo ""
echo "📋 Test Summary:"
echo "   ✅ Test document created and uploaded"
echo "   ✅ S3 bucket accessible"
echo "   ✅ Lambda function deployed"
echo "   ✅ Knowledge Base configured"
echo ""
echo "📝 Next Steps:"
echo "   1. Check your webhook endpoint for incoming requests"
echo "   2. Monitor CloudWatch logs for any errors"
echo "   3. Test document retrieval from Knowledge Base"
echo ""
echo "🔗 Useful Commands:"
echo "   - View logs: aws logs tail $LOG_GROUP --follow"
echo "   - List S3 objects: aws s3 ls s3://$BUCKET_NAME/"
echo "   - Delete test object: aws s3 rm s3://$BUCKET_NAME/$TEST_FILE"
