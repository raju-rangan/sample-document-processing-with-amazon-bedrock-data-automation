IAM_ROLE_ARN = ""

terraform-init:
	cd terraform && terraform init

terraform-apply: terraform-init
	cd terraform && terraform apply --auto-approve

terraform-destroy:
	cd terraform && terraform destroy

agentcore_configure:
	cd src && agentcore configure --entrypoint main.py -er $(IAM_ROLE_ARN)

agentcore_launch:
	cd src && agentcore launch --env AWS_BUCKET_NAME=bedrock-data-automation-store20250802224427805500000002