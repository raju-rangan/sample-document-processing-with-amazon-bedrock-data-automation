provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      ManagedBy   = "terraform"
      CreatedBy   = "document-processing-system"
    }
  }
}

provider "random" {}