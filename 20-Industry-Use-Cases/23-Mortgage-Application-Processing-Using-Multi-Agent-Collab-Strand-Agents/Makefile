NAME = "dev"
IAM_ROLE = "agentcore-dev-iam-role"
ECR = "145023138732.dkr.ecr.us-east-1.amazonaws.com/bedrock_agentcore-dev"
BDA_BUCKET="bedrock-data-automation-store20250802224427805500000002"

terraform-output:
	cd infrastructure/terraform && terraform output

terraform-init:
	cd infrastructure/terraform && terraform init

terraform-apply: terraform-init
	cd infrastructure/terraform && terraform apply --auto-approve -var="agent_name=$(NAME)"

terraform-destroy:
	cd infrastructure/terraform && terraform destroy

agent-configure:
	agentcore configure --entrypoint main.py -er $(IAM_ROLE) -ecr $(ECR)

agent-launch:
	agentcore launch --env AWS_BUCKET_NAME=$(BDA_BUCKET)