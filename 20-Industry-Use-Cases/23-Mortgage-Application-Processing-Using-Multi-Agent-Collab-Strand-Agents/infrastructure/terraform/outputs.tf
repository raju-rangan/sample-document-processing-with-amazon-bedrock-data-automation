output "raw_s3_bucket_name" {
    description = "The name of the raw bucket"
    value       = module.raw_s3_bucket.s3_bucket_id
}

output "bda_s3_bucket_name" {
    description = "The name of the BDA bucket"
    value       = module.bda_s3_bucket.s3_bucket_id
}

output "agentcore_iam_role_name" {
    description = "The name of the IAM role for agentcore"
    value       = aws_iam_role.agentcore_role.name
}

output "agentcore_ecr_repository_url" {
    description = "The name of the ECR repo url for agentcore"
    value       = module.agentcore_ecr.repository_url
}

output "mortgage_api_url" {
    description = "The URL of the mortgage applications HTTP API"
    value       = module.apigateway-v2.api_endpoint
}

output "mortgage_crud_function_name" {
    description = "The name of the mortgage applications Lambda function"
    value       = module.mortgage_applications_lambda.lambda_function_name
}

output "mortgage_preprocessor_function_name" {
    description = "The name of the mortgage applications preprocessor Lambda function"
    value       = module.mortgage_applications_preprocessor_lambda.lambda_function_name
}

