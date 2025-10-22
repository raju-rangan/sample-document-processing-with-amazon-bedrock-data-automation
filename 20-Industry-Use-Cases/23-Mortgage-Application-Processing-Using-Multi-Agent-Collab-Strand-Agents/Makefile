NAME = "dev"
IAM_ROLE = "agentcore-dev-iam-role"
ECR = "145023138732.dkr.ecr.us-east-1.amazonaws.com/bedrock_agentcore-dev"
BDA_BUCKET="bedrock-data-automation-store20250802224427805500000002"

.PHONY: help terraform-output terraform-init terraform-apply terraform-destroy agent-configure agent-launch demo-prep clean update-deps

terraform-output: ## Show terraform outputs
	cd infrastructure/terraform && terraform output

terraform-init: ## Initialize terraform
	cd infrastructure/terraform && terraform init -upgrade

terraform-apply: terraform-init ## Apply terraform configuration
	cd infrastructure/terraform && terraform apply --auto-approve -var="agent_name=$(NAME)"

terraform-destroy: ## Destroy terraform infrastructure
	cd infrastructure/terraform && terraform destroy --auto-approve

agent-configure: ## Configure AgentCore
	source .venv/bin/activate && agentcore configure --entrypoint main.py -er $(IAM_ROLE) -ecr $(ECR)

agent-launch: ## Launch agent to AWS
	source .venv/bin/activate && agentcore launch --env AWS_BUCKET_NAME=$(BDA_BUCKET)

update-deps: ## Update Python dependencies
	uv sync --upgrade