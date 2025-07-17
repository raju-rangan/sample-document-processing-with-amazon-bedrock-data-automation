# Document Processing System - Terraform Makefile
# Usage: make <target> ENV=<dev|prod>

# Default environment
ENV ?= dev

# Terraform directory
TF_DIR = terraform
TF_VAR_FILE = environments/$(ENV)/terraform.tfvars

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help init plan apply destroy validate format clean test-upload logs

# Default target
help: ## Show this help message
	@echo "$(GREEN)Document Processing System - Terraform Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC) make <target> ENV=<dev|prod>"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make init ENV=dev"
	@echo "  make plan ENV=dev"
	@echo "  make apply ENV=prod"

init: ## Initialize Terraform
	@echo "$(GREEN)Initializing Terraform for $(ENV) environment...$(NC)"
	@cd $(TF_DIR) && terraform init

validate: ## Validate Terraform configuration
	@echo "$(GREEN)Validating Terraform configuration...$(NC)"
	@cd $(TF_DIR) && terraform validate
	@echo "$(GREEN)✓ Configuration is valid$(NC)"

format: ## Format Terraform files
	@echo "$(GREEN)Formatting Terraform files...$(NC)"
	@cd $(TF_DIR) && terraform fmt -recursive
	@echo "$(GREEN)✓ Files formatted$(NC)"

plan: validate ## Plan Terraform deployment
	@echo "$(GREEN)Planning Terraform deployment for $(ENV) environment...$(NC)"
	@if [ ! -f "$(TF_DIR)/$(TF_VAR_FILE)" ]; then \
		echo "$(RED)Error: $(TF_VAR_FILE) not found$(NC)"; \
		exit 1; \
	fi
	@cd $(TF_DIR) && terraform plan -var-file="$(TF_VAR_FILE)"

apply: validate ## Apply Terraform configuration
	@echo "$(GREEN)Applying Terraform configuration for $(ENV) environment...$(NC)"
	@if [ ! -f "$(TF_DIR)/$(TF_VAR_FILE)" ]; then \
		echo "$(RED)Error: $(TF_VAR_FILE) not found$(NC)"; \
		exit 1; \
	fi
	@cd $(TF_DIR) && terraform apply -var-file="$(TF_VAR_FILE)"

destroy: ## Destroy Terraform infrastructure
	@echo "$(YELLOW)⚠️  WARNING: This will destroy all infrastructure for $(ENV) environment!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel, or Enter to continue...$(NC)"
	@read
	@cd $(TF_DIR) && terraform destroy -var-file="$(TF_VAR_FILE)"

output: ## Show Terraform outputs
	@echo "$(GREEN)Terraform outputs for $(ENV) environment:$(NC)"
	@cd $(TF_DIR) && terraform output

clean: ## Clean Terraform temporary files
	@echo "$(GREEN)Cleaning Terraform temporary files...$(NC)"
	@cd $(TF_DIR) && rm -f *.tfplan *.zip
	@echo "$(GREEN)✓ Temporary files cleaned$(NC)"

test-upload: ## Upload test document to S3 bucket
	@echo "$(GREEN)Uploading test document...$(NC)"
	@BUCKET_NAME=$$(cd $(TF_DIR) && terraform output -raw document_bucket_name 2>/dev/null); \
	if [ -z "$$BUCKET_NAME" ]; then \
		echo "$(RED)Error: Could not get bucket name. Is infrastructure deployed?$(NC)"; \
		exit 1; \
	fi; \
	TEST_FILE="test-doc-$$(date +%s).txt"; \
	echo "Test document created on $$(date)" > $$TEST_FILE; \
	echo "Environment: $(ENV)" >> $$TEST_FILE; \
	echo "Bucket: $$BUCKET_NAME" >> $$TEST_FILE; \
	aws s3 cp $$TEST_FILE s3://$$BUCKET_NAME/ && \
	echo "$(GREEN)✓ Test document uploaded: $$TEST_FILE$(NC)" && \
	rm -f $$TEST_FILE

logs: ## Show Lambda function logs
	@echo "$(GREEN)Showing Lambda function logs...$(NC)"
	@FUNCTION_NAME=$$(cd $(TF_DIR) && terraform output -raw lambda_function_name 2>/dev/null); \
	if [ -z "$$FUNCTION_NAME" ]; then \
		echo "$(RED)Error: Could not get function name. Is infrastructure deployed?$(NC)"; \
		exit 1; \
	fi; \
	aws logs tail "/aws/lambda/$$FUNCTION_NAME" --follow

status: ## Show infrastructure status
	@echo "$(GREEN)Infrastructure Status for $(ENV) environment:$(NC)"
	@echo ""
	@cd $(TF_DIR) && \
	BUCKET_NAME=$$(terraform output -raw document_bucket_name 2>/dev/null || echo "Not deployed"); \
	LAMBDA_NAME=$$(terraform output -raw lambda_function_name 2>/dev/null || echo "Not deployed"); \
	KB_ID=$$(terraform output -raw knowledge_base_id 2>/dev/null || echo "Not deployed"); \
	echo "$(YELLOW)Document Bucket:$(NC) $$BUCKET_NAME"; \
	echo "$(YELLOW)Lambda Function:$(NC) $$LAMBDA_NAME"; \
	echo "$(YELLOW)Knowledge Base ID:$(NC) $$KB_ID"

# Development shortcuts
dev-init: ## Initialize development environment
	@$(MAKE) init ENV=dev

dev-plan: ## Plan development deployment
	@$(MAKE) plan ENV=dev

dev-apply: ## Apply development configuration
	@$(MAKE) apply ENV=dev

dev-destroy: ## Destroy development infrastructure
	@$(MAKE) destroy ENV=dev

# Production shortcuts
prod-init: ## Initialize production environment
	@$(MAKE) init ENV=prod

prod-plan: ## Plan production deployment
	@$(MAKE) plan ENV=prod

prod-apply: ## Apply production configuration
	@$(MAKE) apply ENV=prod

prod-destroy: ## Destroy production infrastructure
	@$(MAKE) destroy ENV=prod

# Quick development workflow
dev: dev-init dev-plan dev-apply ## Complete development deployment (init + plan + apply)

# All-in-one commands
check: format validate ## Format and validate configuration

deploy: init plan apply ## Complete deployment (init + plan + apply)

# Integration test
test: test-upload ## Run integration test by uploading a document
	@echo "$(GREEN)Integration test completed. Check logs with: make logs ENV=$(ENV)$(NC)"
