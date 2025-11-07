# Terraform Provider Configuration

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Backend configuration for remote state
  # Uncomment and configure for production use
  # backend "s3" {
  #   bucket         = "prime-spark-terraform-state"
  #   key            = "infrastructure/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "PrimeSparkAI"
    }
  }
}

# Secondary region provider for disaster recovery
provider "aws" {
  alias  = "secondary"
  region = var.aws_secondary_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "PrimeSparkAI"
      Region      = "secondary"
    }
  }
}
