data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

# Public subnets only, no NAT gateway, to keep the cost low.
# Nodes get public IPs and reach the internet through the IGW.
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.7.3"

  name = var.vpc_name
  cidr = var.vpc_cidr

  azs            = local.azs
  public_subnets = var.public_subnet_cidrs

  map_public_ip_on_launch = true
  enable_nat_gateway      = false
  enable_dns_hostnames    = true
  enable_dns_support      = true

  # Lets the AWS load balancer integration find these subnets.
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
}
