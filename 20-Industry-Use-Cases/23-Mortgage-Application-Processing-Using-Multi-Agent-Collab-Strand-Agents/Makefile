NAME = "dev"
IAM_ROLE = "agentcore-dev-iam-role"
ECR = "145023138732.dkr.ecr.us-east-1.amazonaws.com/bedrock_agentcore-dev"
BDA_BUCKET="bedrock-data-automation-store20250802224427805500000002"

.PHONY: terraform-output terraform-init terraform-apply terraform-destroy agent-configure agent-launch update-deps upload-docs

terraform-output:
	cd infrastructure/terraform && terraform output

terraform-init:
	cd infrastructure/terraform && terraform init -upgrade

terraform-apply: terraform-init
	cd infrastructure/terraform && terraform apply --auto-approve -var="agent_name=$(NAME)"

terraform-destroy:
	cd infrastructure/terraform && terraform destroy --auto-approve

agent-configure:
	source .venv/bin/activate && agentcore configure --entrypoint ./src/mortgage_processor/ -er $(IAM_ROLE) -ecr $(ECR)

agent-launch:
	source .venv/bin/activate && agentcore launch --local-build --auto-update-on-conflict --env AWS_BUCKET_NAME=$(BDA_BUCKET)

update-deps:
	uv sync --upgrade

upload-docs:
	@echo "Uploading documents to S3 bucket for processing..."
	aws s3 cp documents/ s3://$(shell cd infrastructure/terraform && terraform output -raw raw_s3_bucket_name)/ --recursive --exclude "*" --include "*.pdf"

create-gateway:
	source .venv/bin/activate && python ./src/mortgage_processor/scripts/create_mcp_gateway.py 