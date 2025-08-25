NAME = "dev"
IAM_ROLE = "agentcore-dev-iam-role"
ECR = "145023138732.dkr.ecr.us-east-1.amazonaws.com/bedrock_agentcore-dev"
BDA_BUCKET="bedrock-data-automation-store20250802224427805500000002"

terraform-output:
	cd terraform && terraform output

terraform-init:
	cd terraform && terraform init

terraform-apply: terraform-init
	cd terraform && terraform apply --auto-approve -var="agent_name=$(NAME)"

terraform-destroy:
	cd terraform && terraform destroy

agent-configure:
	agentcore configure --entrypoint main.py -er $(IAM_ROLE) -ecr $(ECR) --requirements-file requirements.txt

agent-launch:
	agentcore launch --env AWS_BUCKET_NAME=$(BDA_BUCKET)

agent-invoke:
	agentcore invoke '{ "bucket": "raw-document-store20250802224425881600000001", "key": "-3195903774208638100.pdf" }'