variable "aws_region" {
  description = "AWS region to create the bucket in"
  type        = string
  default     = "ap-south-1"
}

variable "bucket_prefix" {
  description = "Start of the bucket name, a random suffix is added to keep it unique"
  type        = string
  default     = "srinidhi-24bcs10037-s18-"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,40}$", var.bucket_prefix))
    error_message = "Use only lowercase letters, numbers and hyphens (3-41 characters)."
  }
}

variable "environment" {
  description = "Environment name used in tags"
  type        = string
  default     = "dev"
}
