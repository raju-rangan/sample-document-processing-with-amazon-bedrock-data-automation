#

![architecture](./assets/arch.drawio.png)

## Getting Started

### Deploy infrastructure

```sh
make terraform-apply
```

The output should look something like that:
```
agentcore_iam_role_name = "agentcore-main-iam-role"
bda_s3_bucket_name = "bedrock-data-automation-store**************"
kb_s3_bucket_name = "bedrock-knowledge-base-store**************"
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
'{ "bucket": "raw-document-store20250802224425881600000001", "key": "-3195903774208638100.pdf" }'
### Test the agent
