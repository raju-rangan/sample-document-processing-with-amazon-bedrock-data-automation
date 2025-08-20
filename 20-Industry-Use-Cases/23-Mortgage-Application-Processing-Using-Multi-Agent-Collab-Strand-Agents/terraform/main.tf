data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

module "raw_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 5.2.0"

  bucket_prefix = "raw-document-store"
  acl    = "private"
  force_destroy = true

  control_object_ownership = true
  object_ownership         = "ObjectWriter"
}

module "bda_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 5.2.0"

  bucket_prefix = "bedrock-data-automation-store"
  acl    = "private"
  force_destroy = true
  
  control_object_ownership = true
  object_ownership         = "ObjectWriter"
}

module "kb_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 5.2.0"

  bucket_prefix = "bedrock-knowledge-base-store"
  acl    = "private"
  force_destroy = true
  
  control_object_ownership = true
  object_ownership         = "ObjectWriter"
}

module "applications_dynamodb_table" {
  source   = "terraform-aws-modules/dynamodb-table/aws"
  version = "~> 5.0.0"

  name     = "mortgage-applications"
  hash_key = "application_id"

  attributes = [
    {
      name = "application_id"
      type = "S"
    },
    {
      name = "borrower_name" 
      type = "S"
    },
    {
      name = "status"
      type = "S"
    },
    {
      name = "application_date"
      type = "S"
    },
    {
      name = "loan_originator_id"
      type = "S"
    },
    {
      name = "property_state"
      type = "S"
    },
    {
      name = "loan_amount"
      type = "N"
    },
    {
      name = "ssn"
      type = "S"
    }
  ]

  global_secondary_indexes = [
    {
      name            = "borrower-name-index"
      hash_key        = "borrower_name"
      projection_type = "ALL"
    },
    {
      name            = "status-date-index"
      hash_key        = "status"
      range_key       = "application_date"
      projection_type = "ALL"
    },
    {
      name            = "loan-originator-index"
      hash_key        = "loan_originator_id"
      range_key       = "application_date"
      projection_type = "ALL"
    },
    {
      name            = "property-state-index"
      hash_key        = "property_state"
      range_key       = "application_date"
      projection_type = "KEYS_ONLY"
    },
    {
      name            = "loan-amount-index"
      hash_key        = "status"
      range_key       = "loan_amount"
      projection_type = "KEYS_ONLY"
    },
    {
      name            = "ssn-lookup-index"
      hash_key        = "ssn"
      projection_type = "ALL"
    }
  ]

  billing_mode = "PAY_PER_REQUEST"
  point_in_time_recovery_enabled = true
  server_side_encryption_enabled = true

  tags = {
    Terraform   = "true"
  }
}

resource "aws_iam_role" "agentcore_role" {
  name = "agentcore-${var.agent_name}-iam-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "AssumeRolePolicy"
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock-agentcore:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:*"
          }
        }
      }
    ]
  })

  tags = {
    Terraform   = "true"
  }
}

resource "aws_iam_role_policy" "agentcore_policy" {
  name = "agentcore-${var.agent_name}-policy"
  role = aws_iam_role.agentcore_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "BedrockPermissions"
        Effect = "Allow"
        Action = [
          "bedrock:*",
        ]
        Resource = "*"
      },
      {
        Sid = "ECRImageAccess"
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        Resource = "arn:aws:ecr:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:repository/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogStreams",
          "logs:CreateLogGroup"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
      },
      {
        Effect = "Allow"
        Action = ["logs:DescribeLogGroups"]
        Resource = "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
      },
      {
        Sid = "ECRTokenAccess"
        Effect = "Allow"
        Action = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Resource = "*"
        Action = "cloudwatch:PutMetricData"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "bedrock-agentcore"
          }
        }
      },
      {
        Sid = "GetAgentAccessToken"
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:*",
        ]
        Resource = [
          "*"
        ]
      },
      {
        Sid = "S3AccessRaw"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.raw_s3_bucket.s3_bucket_arn,
          "${module.raw_s3_bucket.s3_bucket_arn}/*"
        ]
      },
      {
        Sid = "S3AccessBDA"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.bda_s3_bucket.s3_bucket_arn,
          "${module.bda_s3_bucket.s3_bucket_arn}/*"
        ]
      },
      {
            Sid = "ListAllS3"
            Effect = "Allow",
            Action = "s3:ListAllMyBuckets",
            Resource = [
              "arn:aws:s3:::*"
            ]
      },
      {
        Sid = "S3AccessKB"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.kb_s3_bucket.s3_bucket_arn,
          "${module.kb_s3_bucket.s3_bucket_arn}/*"
        ]
      },
      {
        Sid = "DynamoDBAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:BatchGetItem",
          "dynamodb:ListTables",
          "dynamodb:DescribeTable"
        ]
        Resource = [ 
          module.applications_dynamodb_table.dynamodb_table_arn,
          "${module.applications_dynamodb_table.dynamodb_table_arn}/index/*"
        ]
      }
    ]
  })
  
}

module "agentcore_ecr" {
  source = "terraform-aws-modules/ecr/aws"
  version = "~> 2.4.0"

  repository_name = "bedrock_agentcore-${var.agent_name}"

  repository_read_write_access_arns = [aws_iam_role.agentcore_role.arn]

  repository_image_tag_mutability = "MUTABLE"
  
  repository_lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1,
        description  = "Keep last 30 images",
        selection = {
          tagStatus     = "tagged",
          tagPrefixList = ["v"],
          countType     = "imageCountMoreThan",
          countNumber   = 30
        },
        action = {
          type = "expire"
        }
      }
    ]
  })

  tags = {
    Terraform   = "true"
  }
}

module "mortgage_applications_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0"

  function_name = "mortgage-applications-crud"
  description   = "CRUD operations for mortgage applications"
  handler       = "main.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256
  publish       = true

  source_path = "${path.module}/lambda"

  environment_variables = {
    TABLE_NAME = "mortgage-applications"
  }

  attach_policy_statements = true
  policy_statements = {
    dynamodb = {
      effect = "Allow"
      actions = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ]
      resources = [
        "arn:aws:dynamodb:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:table/mortgage-applications",
        "arn:aws:dynamodb:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:table/mortgage-applications/index/*"
      ]
    }
  }

  cloudwatch_logs_retention_in_days = 14

  create_lambda_function_url = false
  
  tags = {
    Name        = "mortgage-applications-crud"
    Environment = "production"
    Terraform   = "true"
  }
}