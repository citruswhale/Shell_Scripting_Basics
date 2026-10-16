terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }

  # State stays local for this student lab. terraform.tfstate is
  # gitignored and must never be committed (it can hold sensitive data).
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "gearloan-capstone"
      Owner     = "srinidhi-24bcs10037"
      ManagedBy = "terraform"
    }
  }
}
