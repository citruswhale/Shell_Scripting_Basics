terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.9"
    }
  }

  # State is kept locally for this lab. terraform.tfstate is gitignored
  # and must never be committed.
}

provider "aws" {
  region = var.aws_region

  # Every resource gets these tags automatically.
  default_tags {
    tags = {
      Project     = "s18-terraform-s3-demo"
      Owner       = "srinidhi-24bcs10037"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}
