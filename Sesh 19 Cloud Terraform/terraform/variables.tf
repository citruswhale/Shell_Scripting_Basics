variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Name prefix used for resources"
  type        = string
  default     = "gearloan-s19"
}

variable "instance_type" {
  description = "EC2 instance type for the web server"
  type        = string
  default     = "t3.micro"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.20.1.0/24"
}

variable "admin_cidr" {
  description = "CIDR allowed to SSH (e.g. 1.2.3.4/32). Empty means no SSH rule at all."
  type        = string
  default     = ""
}
