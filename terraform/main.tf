# 1. Define AWS Cloud Provider settings
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 2. Build your private Amazon ECR repository for the backtest application
resource "aws_ecr_repository" "backtest_repo" {
  name                 = "backtest-upstox-app"
  image_tag_mutability = "MUTABLE"

  # Production Guard: Automatically scans images for OS bugs upon delivery
  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS" # Uses AWS Key Management Service to encrypt your code layers at rest
  }

  tags = {
    Environment = "Development"
    Project     = "Backtest-Automation"
  }
}
