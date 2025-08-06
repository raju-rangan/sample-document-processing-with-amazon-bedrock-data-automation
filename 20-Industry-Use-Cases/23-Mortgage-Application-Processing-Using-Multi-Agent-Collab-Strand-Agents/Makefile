NAME = "dev"
IAM_ROLE = ""
ECR = ""
BDA_BUCKET="bedrock-data-automation-store20250802224427805500000002"

terraform-init:
	cd terraform && terraform init

terraform-apply: terraform-init
	cd terraform && terraform apply --auto-approve -var="agent_name=$(NAME)"

terraform-destroy:
	cd terraform && terraform destroy

agent-configure:
	cd src && agentcore configure --entrypoint main.py -er $(IAM_ROLE) -ecr $(ECR) --requirements-file requirements.txt

agent-launch:
	cd src && agentcore launch --env AWS_BUCKET_NAME=$(BDA_BUCKET)