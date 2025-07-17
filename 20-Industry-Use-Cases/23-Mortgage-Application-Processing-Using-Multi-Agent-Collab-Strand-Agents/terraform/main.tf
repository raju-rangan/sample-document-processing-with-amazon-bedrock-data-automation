# Random suffix for unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Local values for resource naming
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  bucket_suffix = random_id.bucket_suffix.hex
  
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.additional_tags
  )
}

#######################
# S3 Buckets
#######################

# Document Storage S3 Bucket
resource "aws_s3_bucket" "document_storage" {
  bucket = "${local.name_prefix}-${var.document_bucket_name}-${local.bucket_suffix}"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-document-storage"
    Type = "DocumentStorage"
  })
}

# Document Storage Bucket Configuration
resource "aws_s3_bucket_versioning" "document_storage" {
  bucket = aws_s3_bucket.document_storage.id
  versioning_configuration {
    status = var.enable_s3_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "document_storage" {
  bucket = aws_s3_bucket.document_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "document_storage" {
  bucket = aws_s3_bucket.document_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle configuration for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "document_storage" {
  bucket = aws_s3_bucket.document_storage.id

  rule {
    id     = "document_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

# Vector Storage S3 Bucket
resource "aws_s3_bucket" "vector_storage" {
  bucket = "${local.name_prefix}-${var.vector_bucket_name}-${local.bucket_suffix}"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vector-storage"
    Type = "VectorStorage"
  })
}

# Vector Storage Bucket Configuration
resource "aws_s3_bucket_versioning" "vector_storage" {
  bucket = aws_s3_bucket.vector_storage.id
  versioning_configuration {
    status = var.enable_s3_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "vector_storage" {
  bucket = aws_s3_bucket.vector_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "vector_storage" {
  bucket = aws_s3_bucket.vector_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

#######################
# IAM Roles and Policies
#######################

# Lambda Execution Role
resource "aws_iam_role" "lambda_execution_role" {
  name = "${local.name_prefix}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Lambda Execution Policy
resource "aws_iam_role_policy" "lambda_execution_policy" {
  name = "${local.name_prefix}-lambda-execution-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:HeadObject"
        ]
        Resource = [
          "${aws_s3_bucket.document_storage.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "${aws_s3_bucket.vector_storage.arn}/*"
        ]
      }
    ]
  })
}

# Bedrock Service Role
resource "aws_iam_role" "bedrock_service_role" {
  name = "${local.name_prefix}-bedrock-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Bedrock Service Policy
resource "aws_iam_role_policy" "bedrock_service_policy" {
  name = "${local.name_prefix}-bedrock-service-policy"
  role = aws_iam_role.bedrock_service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.vector_storage.arn,
          "${aws_s3_bucket.vector_storage.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = var.bedrock_model_arn
      }
    ]
  })
}

#######################
# EventBridge Configuration
#######################

# EventBridge Rule for S3 Object Creation
resource "aws_cloudwatch_event_rule" "document_upload" {
  name        = "${local.name_prefix}-document-upload-rule"
  description = "Trigger when documents are uploaded to S3"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [aws_s3_bucket.document_storage.bucket]
      }
    }
  })

  tags = local.common_tags
}

# EventBridge Target - Lambda Function
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.document_upload.name
  target_id = "DocumentProcessorLambdaTarget"
  arn       = aws_lambda_function.document_processor.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.document_processor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.document_upload.arn
}

#######################
# Lambda Function
#######################

# Lambda function code archive
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/document_processor.zip"
  source {
    content = templatefile("${path.module}/lambda/document_processor.py", {
      webhook_url = var.webhook_url
    })
    filename = "index.py"
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.name_prefix}-document-processor"
  retention_in_days = 14

  tags = local.common_tags
}

# Lambda function
resource "aws_lambda_function" "document_processor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.name_prefix}-document-processor"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 60
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      WEBHOOK_URL = var.webhook_url
      VECTOR_BUCKET = aws_s3_bucket.vector_storage.bucket
      DOCUMENT_BUCKET = aws_s3_bucket.document_storage.bucket
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_execution_policy,
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = local.common_tags
}

#######################
# S3 Event Notification
#######################

# S3 Bucket Notification to EventBridge
resource "aws_s3_bucket_notification" "document_upload_notification" {
  bucket      = aws_s3_bucket.document_storage.id
  eventbridge = true
}
