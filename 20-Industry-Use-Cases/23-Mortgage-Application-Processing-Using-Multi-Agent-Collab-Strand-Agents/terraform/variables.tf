# Project Configuration
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "document-processing"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

# S3 Configuration
variable "document_bucket_name" {
  description = "Name for the document storage S3 bucket (will be made unique)"
  type        = string
  default     = "document-storage"
}

variable "vector_bucket_name" {
  description = "Name for the vector storage S3 bucket (will be made unique)"
  type        = string
  default     = "vector-storage"
}

variable "enable_s3_versioning" {
  description = "Enable versioning on S3 buckets"
  type        = bool
  default     = true
}

# EventBridge Configuration
variable "webhook_url" {
  description = "HTTP webhook URL to call when documents are uploaded"
  type        = string
  default     = "https://webhook.site/unique-id"
}

# Bedrock Configuration
variable "bedrock_model_arn" {
  description = "ARN of the Bedrock embedding model"
  type        = string
  default     = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
}

variable "knowledge_base_name" {
  description = "Name for the Bedrock Knowledge Base"
  type        = string
  default     = "document-kb"
}

# Tagging
variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
