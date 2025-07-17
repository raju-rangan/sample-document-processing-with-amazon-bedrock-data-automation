# Document Processing System - Simple Makefile

.PHONY: help init plan apply destroy clean test logs

help: ## Show available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

init: ## Initialize Terraform
	cd terraform && terraform init

plan: ## Plan Terraform deployment
	cd terraform && terraform plan -var-file="environments/dev/terraform.tfvars"

apply: ## Apply Terraform configuration
	cd terraform && terraform apply -var-file="environments/dev/terraform.tfvars"

destroy: ## Destroy infrastructure
	cd terraform && terraform destroy -var-file="environments/dev/terraform.tfvars"

clean: ## Clean temporary files
	cd terraform && rm -f *.tfplan *.zip

test: ## Upload test document
	@BUCKET=$$(cd terraform && terraform output -raw document_bucket_name 2>/dev/null); \
	if [ -n "$$BUCKET" ]; then \
		echo "Test doc" > test.txt && \
		aws s3 cp test.txt s3://$$BUCKET/ && \
		rm test.txt && \
		echo "Test document uploaded to $$BUCKET"; \
	else \
		echo "Error: Infrastructure not deployed"; \
	fi

logs: ## Show Lambda logs
	@FUNC=$$(cd terraform && terraform output -raw lambda_function_name 2>/dev/null); \
	if [ -n "$$FUNC" ]; then \
		aws logs tail "/aws/lambda/$$FUNC" --follow; \
	else \
		echo "Error: Lambda function not found"; \
	fi
