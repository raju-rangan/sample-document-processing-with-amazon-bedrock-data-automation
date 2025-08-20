#!/usr/bin/env bash
set -euo pipefail

# Default values (can be overridden by CLI args)
DEFAULT_PROJECT_ARN="arn:aws:bedrock:us-east-1:145023138732:data-automation-project/63749ca89ee7"
DEFAULT_S3_INPUT_URI="s3://raw-document-store20250802224425881600000001/-3195903774208638100.pdf"
DEFAULT_S3_OUTPUT_URI="s3://bedrock-data-automation-store20250802224427805500000002/"
DEFAULT_PROFILE_ARN="arn:aws:bedrock:us-east-1:145023138732:data-automation-profile/us.data-automation-v1"
DEFAULT_STAGE="LIVE"
DEFAULT_REGION="us-east-1"

PROJECT_ARN="${1:-$DEFAULT_PROJECT_ARN}"
S3_INPUT_URI="${2:-$DEFAULT_S3_INPUT_URI}"
S3_OUTPUT_URI="${3:-$DEFAULT_S3_OUTPUT_URI}"
PROFILE_ARN="${4:-$DEFAULT_PROFILE_ARN}"
STAGE="${5:-$DEFAULT_STAGE}"
REGION="${6:-$DEFAULT_REGION}"

echo "Invoking Bedrock Data Automation (runtime)..."
echo "  Project ARN     : $PROJECT_ARN"
echo "  Input S3 URI    : $S3_INPUT_URI"
echo "  Output S3 URI   : $S3_OUTPUT_URI"
echo "  Profile ARN     : $PROFILE_ARN"
echo "  Stage           : $STAGE"
echo "  Region          : $REGION"

RESPONSE=$(aws bedrock-data-automation-runtime invoke-data-automation-async \
  --input-configuration "{\"s3Uri\":\"$S3_INPUT_URI\"}" \
  --output-configuration "{\"s3Uri\":\"$S3_OUTPUT_URI\"}" \
  --data-automation-configuration "{\"dataAutomationProjectArn\":\"$PROJECT_ARN\",\"stage\":\"$STAGE\"}" \
  --data-automation-profile-arn "$PROFILE_ARN" \
  --region "$REGION")

echo "Response:"
echo "$RESPONSE"