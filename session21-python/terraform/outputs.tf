output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "region" {
  value = var.aws_region
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnets
}

output "node_group_name" {
  value = module.eks.eks_managed_node_groups["default"].node_group_id
}

output "configure_kubectl" {
  description = "Run this to point kubectl at the cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name} --profile devops-lab"
}

output "storage_note" {
  value = "EBS CSI driver is installed. Create a gp3 default StorageClass and install metrics-server with kubectl/Helm after the cluster is up. Delete LoadBalancer Services and PVCs before terraform destroy."
}
