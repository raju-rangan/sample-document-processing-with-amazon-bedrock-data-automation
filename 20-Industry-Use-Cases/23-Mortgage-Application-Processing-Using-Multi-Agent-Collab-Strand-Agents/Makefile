.PHONY: help init plan apply destroy clean test logs

help: ## Show available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

init: ## Initialize Terraform
	cd terraform && terraform init

plan: ## Plan Terraform deployment
	cd terraform && terraform plan

apply: ## Apply Terraform configuration
	cd terraform && terraform apply

destroy: ## Destroy infrastructure
	cd terraform && terraform destroy