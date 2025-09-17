#

![architecture](./assets/arch.drawio.png)

## Getting Started

### Deploy infrastructure

```sh
make terraform-apply
```

The output should look something like that:
```
agentcore_ecr_repository_url = "************.dkr.ecr.us-east-1.amazonaws.com/bedrock_agentcore-dev"
agentcore_iam_role_name = "agentcore-dev-iam-role"
bda_s3_bucket_name = "bedrock-data-automation-store**************"
mortgage_api_url = "https://************.us-east-1.amazonaws.com"
mortgage_crud_function_name = "mortgage-applications-crud"
mortgage_preprocessor_function_name = "mortgage-preprocess"
raw_s3_bucket_name = "raw-document-store**************"
```

### Deploy Agent via AgentCore
Using the `agentcore_iam_role_name` output configure and deploy the agentcore:

```sh
agentcore configure --entrypoint main.py -er agentcore-main-iam-role
```

And launch it to AWS:
```sh
agentcore launch
```

### Test the agent
