output "raw_s3_bucket_name" {
    description = "The name of the raw bucket"
    value       = module.raw_s3_bucket.s3_bucket_id
}

output "bda_s3_bucket_name" {
    description = "The name of the BDA bucket"
    value       = module.bda_s3_bucket.s3_bucket_id
}

output "kb_s3_bucket_name" {
    description = "The name of the KB bucket"
    value       = module.kb_s3_bucket.s3_bucket_id
}

output "agentcore_iam_role_name" {
    description = "The name of the IAM role for agentcore"
    value       = aws_iam_role.agentcore_role.name
}

output "agentcore_ecr_repository_url" {
    description = "The name of the ECR repo url for agentcore"
    value       = module.agentcore_ecr.repository_url
}

