data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

module "raw_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 5.5.0"

  bucket_prefix = "raw-document-store"
  acl    = "private"
  force_destroy = true

  control_object_ownership = true
  object_ownership         = "ObjectWriter"
}

resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.mortgage_applications_preprocessor_lambda.lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = module.raw_s3_bucket.s3_bucket_arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = module.raw_s3_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.mortgage_applications_preprocessor_lambda.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
}

module "bda_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 5.5.0"

  bucket_prefix = "bedrock-data-automation-store"
  acl    = "private"
  force_destroy = true
  
  control_object_ownership = true
  object_ownership         = "ObjectWriter"
}

module "kb_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 5.5.0"

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
      name            = "loan-originator-index"
      hash_key        = "loan_originator_id"
      projection_type = "ALL"
    },
    {
      name            = "property-state-index"
      hash_key        = "property_state"
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
  version = "~> 8.0.1"

  function_name = "mortgage-applications-crud"
  description   = "CRUD operations for mortgage applications"
  handler       = "main.lambda_handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 256
  publish       = true

  source_path = "${path.module}/lambdas/crud_lambda"

  environment_variables = {
    TABLE_NAME = "mortgage-applications"
    SPEC_S3_URI = "s3://amitzaf-mortgage-demo-bucket/specs/openapi_spec.json"
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
    Terraform   = "true"
  }
}

module "eventbridge" {
  source = "terraform-aws-modules/eventbridge/aws"
  version = "4.1.0"

  create_bus = false

  rules = {
    bda = {
      description   = "Capture all BDA data"
      enabled       = true
      event_pattern = jsonencode({ "source" : ["aws.bedrock"], "detail-type": ["Bedrock Data Automation Job Succeeded"] })
    }
  }

  targets = {
    bda = [
      {
        name            = "send-bda-to-lambda"
        arn             = module.mortgage_applications_agentcore_lambda.lambda_function_arn
      },
    ]
  }

  tags = {
    Name = "my-bus"
  }
}

module "mortgage_applications_agentcore_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0.1"

  function_name = "mortgage-agentcore"
  description   = "Mortgage application agentcore"
  handler       = "main.lambda_handler"
  runtime       = "python3.13"
  timeout       = 900
  memory_size   = 256
  publish       = true

  source_path = "${path.module}/lambdas/agentcore_lambda"

  environment_variables = {
    AGENT_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:145023138732:runtime/dev-7IRV2WDSok"
    AGENT_ENDPOINT_NAME = "DEFAULT"
  }

  attach_policy_statements = true
  policy_statements = {
    bedrock_agent_core = {
      effect = "Allow"
      actions = [
        "bedrock-agentcore:*"
      ]
      resources = ["*"]
    }

    bedrock_data_automation = {
      effect = "Allow"
      actions = [
        "bedrock:*"
      ]
      resources = ["*"]
    }

    s3_read_only = {
      effect = "Allow"
      actions = [
        "s3:Get*",
        "s3:List*",
      ]
      resources = [
        "arn:aws:s3:::*",
        "arn:aws:s3:::*/*"
      ]
    }
  }

  cloudwatch_logs_retention_in_days = 14

  create_lambda_function_url = false
  
  tags = {
    Name        = "mortgage-applications-agentcore"
    Terraform   = "true"
  }

  allowed_triggers = {
    AllowEventBridgeInvocation = {
      principal  = "events.amazonaws.com"
      source_arn = module.eventbridge.eventbridge_rule_arns["bda"]
    }
  }
}

module "mortgage_applications_preprocessor_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0.1"

  function_name = "mortgage-preprocess"
  description   = "Mortgage application preprocessor"
  handler       = "main.lambda_handler"
  runtime       = "python3.13"
  timeout       = 900
  memory_size   = 256
  publish       = true

  source_path = "${path.module}/lambdas/preprocess_lambda"

  environment_variables = {
    BDA_PROFILE_ARN = "arn:aws:bedrock:us-east-1:145023138732:data-automation-profile/us.data-automation-v1"
    BDA_PROJECT_ARN = "arn:aws:bedrock:us-east-1:145023138732:data-automation-project/1feaf1933fd3"
    INPUT_S3_BUCKET = "raw-document-store20250802224425881600000001"
    OUTPUT_S3_BUCKET = "bedrock-data-automation-store20250802224427805500000002"
    AGENT_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:145023138732:runtime/dev-7IRV2WDSok"
    AGENT_ENDPOINT_NAME = "DEFAULT"
  }

  attach_policy_statements = true
  policy_statements = {
    bedrock_agent_core = {
      effect = "Allow"
      actions = [
        "bedrock-agentcore:*"
      ]
      resources = ["*"]
    }

    bedrock_data_automation = {
      effect = "Allow"
      actions = [
        "bedrock:*"
      ]
      resources = ["*"]
    }

    s3_read_only = {
      effect = "Allow"
      actions = [
        "s3:Get*",
        "s3:List*",
        "s3:Put*",
      ]
      resources = [
        "arn:aws:s3:::*",
        "arn:aws:s3:::*/*"
      ]
    }
  }

  cloudwatch_logs_retention_in_days = 14

  create_lambda_function_url = false
  
  tags = {
    Name        = "mortgage-applications-preprocessor"
    Terraform   = "true"
  }
}

module "lambda_authorizer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0.1"

  function_name = "api-gateway-authorizer"
  description   = "Simple API key authorizer for API Gateway"
  handler       = "main.lambda_handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 256
  publish = true

  source_path = "${path.module}/lambdas/lambda_authorizer"

  environment_variables = {
    API_KEY = "aaa"
  }
  
  allowed_triggers = {
    APIGateway = {
      service    = "apigateway"
      source_arn = "${module.apigateway-v2.api_execution_arn}/*/*"
    }
  }

  tags = {
    Terraform = "true"
  }
}

module "apigateway-v2" {
    source  = "terraform-aws-modules/apigateway-v2/aws"
    version = "~> 5.3"

    name          = "mortgage-applications-api"
    description   = "HTTP API Gateway for mortgage applications CRUD operations"

    create_domain_name = false
    create_certificate = false

    cors_configuration = {
      allow_headers     = ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token", "x-amz-user-agent"]
      allow_methods     = ["*"]
      allow_origins     = ["*"]
    }

    authorizers = {
      simple_auth = {
        authorizer_type                   = "REQUEST"
        authorizer_uri                    = module.lambda_authorizer.lambda_function_invoke_arn
        authorizer_payload_format_version = "2.0"
        identity_sources                  = ["$request.header.api_key"]
        name                              = "simple-header-authorizer"
      }
    }

    routes = {
      "POST /applications" = {
        authorizer_key = "simple_auth"
        authorization_type                   = "CUSTOM"

        integration = {
          uri                    = module.mortgage_applications_lambda.lambda_function_arn
          payload_format_version = "2.0"
          timeout_milliseconds   = 12000
        }
      }

      "GET /applications" = {
        authorizer_key = "simple_auth"
        authorization_type                   = "CUSTOM"

        integration = {
          uri                    = module.mortgage_applications_lambda.lambda_function_arn
          payload_format_version = "2.0"
          timeout_milliseconds   = 12000
        }
      }

      "GET /applications/{application_id}" = {
        authorizer_key = "simple_auth"
        authorization_type                   = "CUSTOM"

        integration = {
          uri                    = module.mortgage_applications_lambda.lambda_function_arn
          payload_format_version = "2.0"
          timeout_milliseconds   = 12000
        }
      }

      "PUT /applications/{application_id}" = {
        authorizer_key = "simple_auth"
        authorization_type                   = "CUSTOM"

        integration = {
          uri                    = module.mortgage_applications_lambda.lambda_function_arn
          payload_format_version = "2.0"
          timeout_milliseconds   = 12000
        }
      }

      "DELETE /applications/{application_id}" = {
        authorizer_key = "simple_auth"
        authorization_type                   = "CUSTOM"

        integration = {
          uri                    = module.mortgage_applications_lambda.lambda_function_arn
          payload_format_version = "2.0"
          timeout_milliseconds   = 12000
        }
      }
    }

    tags = {
      Terraform = "true"
    }
  }

resource "aws_lambda_permission" "api_gateway_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = module.mortgage_applications_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${module.apigateway-v2.api_execution_arn}/*/*"
}