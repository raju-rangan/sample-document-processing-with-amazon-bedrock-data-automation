# S3 Bucket Outputs
output "document_bucket_name" {
  description = "Name of the document storage S3 bucket"
  value       = aws_s3_bucket.document_storage.bucket
}

output "document_bucket_arn" {
  description = "ARN of the document storage S3 bucket"
  value       = aws_s3_bucket.document_storage.arn
}

output "vector_bucket_name" {
  description = "Name of the vector storage S3 bucket"
  value       = aws_s3_bucket.vector_storage.bucket
}

output "vector_bucket_arn" {
  description = "ARN of the vector storage S3 bucket"
  value       = aws_s3_bucket.vector_storage.arn
}

# EventBridge Outputs
output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.document_upload.name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.document_upload.arn
}

# Lambda Outputs
output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.document_processor.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.document_processor.arn
}

# Bedrock Knowledge Base Outputs
output "knowledge_base_id" {
  description = "ID of the Bedrock Knowledge Base"
  value       = aws_bedrockagent_knowledge_base.document_kb.id
}

output "knowledge_base_arn" {
  description = "ARN of the Bedrock Knowledge Base"
  value       = aws_bedrockagent_knowledge_base.document_kb.arn
}

# IAM Role Outputs
output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "bedrock_role_arn" {
  description = "ARN of the Bedrock service role"
  value       = aws_iam_role.bedrock_service_role.arn
}
