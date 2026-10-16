variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "gearloan-eks"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version (newest in standard support in ap-south-1)"
  type        = string
  default     = "1.37"
}

variable "vpc_name" {
  description = "VPC name"
  type        = string
  default     = "gearloan-vpc"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.30.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "One public subnet per AZ"
  type        = list(string)
  default     = ["10.30.1.0/24", "10.30.2.0/24"]
}

variable "node_instance_type" {
  description = "Instance type for the worker nodes (x86). The AWS Free plan only allows free-tier types, so m7i-flex.large (2 vCPU, 8 GiB) instead of t3.medium"
  type        = string
  default     = "m7i-flex.large"
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 3
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_disk_size" {
  description = "Root disk size in GB for each node"
  type        = number
  default     = 20
}
