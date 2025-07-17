# S3 Bucket Outputs
output "document_bucket_name" {
  description = "Name of the document storage S3 bucket"
  value       = aws_s3_bucket.document_storage.bucket
}

output "document_bucket_arn" {
  description = "ARN of the document storage S3 bucket"
  value       = aws_s3_bucket.document_storage.arn
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

# Bedrock Knowledge Base Outputs - Commented out temporarily
# output "knowledge_base_id" {
#   description = "ID of the Bedrock Knowledge Base"
#   value       = aws_bedrockagent_knowledge_base.document_kb.id
# }

# output "knowledge_base_arn" {
#   description = "ARN of the Bedrock Knowledge Base"
#   value       = aws_bedrockagent_knowledge_base.document_kb.arn
# }

# OpenSearch Serverless Outputs
output "opensearch_collection_arn" {
  description = "ARN of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.vector_collection.arn
}

output "opensearch_collection_endpoint" {
  description = "Endpoint of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.vector_collection.collection_endpoint
}

# Data Source Outputs - Commented out temporarily
# output "bedrock_data_source_id" {
#   description = "ID of the Bedrock data source"
#   value       = aws_bedrockagent_data_source.document_data_source.data_source_id
# }

# IAM Role Outputs
output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "bedrock_role_arn" {
  description = "ARN of the Bedrock service role"
  value       = aws_iam_role.bedrock_service_role.arn
}
