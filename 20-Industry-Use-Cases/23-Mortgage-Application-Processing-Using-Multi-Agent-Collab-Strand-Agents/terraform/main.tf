# Local values for resource naming
locals {
  common_tags = merge(
    {
      Project     = var.project_name
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
  bucket = "${var.project_name}-${var.document_bucket_name}-${random_id.bucket_suffix.hex}"
  
  tags = merge(local.common_tags, {
    Type = "DocumentStorage"
  })
}

# Random suffix for unique bucket naming
resource "random_id" "bucket_suffix" {
  byte_length = 4
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

#######################
# IAM Roles and Policies
#######################

# Lambda Execution Role
resource "aws_iam_role" "lambda_execution_role" {
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
      }
    ]
  })
}

# Bedrock Service Role
resource "aws_iam_role" "bedrock_service_role" {
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
          aws_s3_bucket.document_storage.arn,
          "${aws_s3_bucket.document_storage.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = var.bedrock_model_arn
      },
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = "*"
      }
    ]
  })
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
  name              = "/aws/lambda/document-processor"
  retention_in_days = 14

  tags = local.common_tags
}

# Lambda function
resource "aws_lambda_function" "document_processor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "document-processor"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "index.handler"
  runtime         = "python3.13"
  timeout         = 60
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      WEBHOOK_URL = var.webhook_url
      DOCUMENT_BUCKET = aws_s3_bucket.document_storage.bucket
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_execution_policy,
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = local.common_tags
}

# Permission for S3 to invoke Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.document_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.document_storage.arn
}

#######################
# S3 Event Notification
#######################

# S3 Bucket Notification to Lambda
resource "aws_s3_bucket_notification" "document_upload_notification" {
  bucket = aws_s3_bucket.document_storage.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.document_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

#######################
# Bedrock Knowledge Base
#######################

# Bedrock Knowledge Base - Commented out temporarily due to index creation issue
# resource "aws_bedrockagent_knowledge_base" "document_kb" {
#   name     = "${var.knowledge_base_name}"
#   role_arn = aws_iam_role.bedrock_service_role.arn
#   
#   knowledge_base_configuration {
#     vector_knowledge_base_configuration {
#       embedding_model_arn = var.bedrock_model_arn
#     }
#     type = "VECTOR"
#   }
#   
#   storage_configuration {
#     type = "OPENSEARCH_SERVERLESS"
#     opensearch_serverless_configuration {
#       collection_arn    = aws_opensearchserverless_collection.vector_collection.arn
#       vector_index_name = "bedrock-knowledge-base-default-index"
#       field_mapping {
#         vector_field   = "bedrock-knowledge-base-default-vector"
#         text_field     = "AMAZON_BEDROCK_TEXT_CHUNK"
#         metadata_field = "AMAZON_BEDROCK_METADATA"
#       }
#     }
#   }

#   depends_on = [
#     aws_opensearchserverless_collection.vector_collection,
#     aws_opensearchserverless_access_policy.vector_collection_access,
#     aws_opensearchserverless_security_policy.vector_collection_encryption,
#     aws_opensearchserverless_security_policy.vector_collection_network
#   ]

#   tags = local.common_tags
# }

# OpenSearch Serverless Collection for vector storage
resource "aws_opensearchserverless_collection" "vector_collection" {
  name = "vector-collection"
  type = "VECTORSEARCH"

  tags = local.common_tags
}

# OpenSearch Serverless Security Policy
resource "aws_opensearchserverless_security_policy" "vector_collection_encryption" {
  name = "vector-collection-encryption"
  type = "encryption"
  policy = jsonencode({
    Rules = [
      {
        Resource = [
          "collection/vector-collection"
        ]
        ResourceType = "collection"
      }
    ]
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_security_policy" "vector_collection_network" {
  name = "vector-collection-network"
  type = "network"
  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/vector-collection"
          ]
          ResourceType = "collection"
        }
      ]
      AllowFromPublic = true
    }
  ])
}

# Data Access Policy for Bedrock
resource "aws_opensearchserverless_access_policy" "vector_collection_access" {
  name = "vector-collection-access"
  type = "data"
  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/vector-collection"
          ]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
          ResourceType = "collection"
        },
        {
          Resource = [
            "index/vector-collection/*"
          ]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
          ResourceType = "index"
        }
      ]
      Principal = [
        aws_iam_role.bedrock_service_role.arn
      ]
    }
  ])
}

# Bedrock Knowledge Base Data Source - Commented out temporarily
# resource "aws_bedrockagent_data_source" "document_data_source" {
#   knowledge_base_id = aws_bedrockagent_knowledge_base.document_kb.id
#   name              = "document-data-source"
#   
#   data_source_configuration {
#     type = "S3"
#     s3_configuration {
#       bucket_arn = aws_s3_bucket.document_storage.arn
#     }
#   }

#   depends_on = [
#     aws_opensearchserverless_collection.vector_collection
#   ]
# }
