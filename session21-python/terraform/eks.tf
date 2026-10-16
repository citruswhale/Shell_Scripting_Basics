module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.29.0"

  name               = var.cluster_name
  kubernetes_version = var.kubernetes_version

  # Public API endpoint so kubectl works from my laptop.
  endpoint_public_access = true

  # The IAM user running terraform (devops-lab) becomes cluster admin
  # through an EKS access entry.
  enable_cluster_creator_admin_permissions = true

  # Keep the lab cheap and easy to destroy:
  # - no customer KMS key (EKS still encrypts secrets with an AWS owned key)
  # - no control plane logs / CloudWatch log group
  # - no IRSA OIDC provider, Pod Identity is used instead
  create_kms_key              = false
  encryption_config           = null
  enabled_log_types           = []
  create_cloudwatch_log_group = false
  enable_irsa                 = false

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnets

  # Only used when the account can't create load balancers: lets the listed
  # IPs reach the ingress-nginx NodePort (30080) on the nodes' public IPs.
  # Empty list (the default) = no extra rule at all.
  node_security_group_additional_rules = merge({
    # Node-to-node on port 80: ingress-nginx listens on 80 inside its Pod, and traffic
    # that lands on another node is forwarded to it. The module's default node-to-node
    # rule only covers ports 1025-65535.
    nodes_to_ingress_pod_http = {
      description = "Node to node, ingress-nginx Pod port 80"
      protocol    = "tcp"
      from_port   = 80
      to_port     = 80
      type        = "ingress"
      self        = true
    }
    }, length(var.ingress_allowed_cidrs) == 0 ? {} : {
    ingress_nodeport_http = {
      description = "ingress-nginx HTTP NodePort from allowed IPs only"
      protocol    = "tcp"
      from_port   = 30080
      to_port     = 30080
      type        = "ingress"
      cidr_blocks = var.ingress_allowed_cidrs
    }
  })

  addons = {
    # These two must be ready before nodes join.
    vpc-cni = {
      before_compute = true
    }
    eks-pod-identity-agent = {
      before_compute = true
    }
    kube-proxy = {}
    coredns    = {}

    # EBS CSI driver so PVCs can create EBS volumes. It gets its IAM
    # role through EKS Pod Identity.
    aws-ebs-csi-driver = {
      pod_identity_association = [{
        role_arn        = aws_iam_role.ebs_csi.arn
        service_account = "ebs-csi-controller-sa"
      }]
    }
  }

  eks_managed_node_groups = {
    default = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = [var.node_instance_type]

      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size

      # Root disk set in the launch template (disk_size is ignored
      # when the module uses its own launch template).
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = var.node_disk_size
            volume_type           = "gp3"
            encrypted             = true
            delete_on_termination = true
          }
        }
      }
    }
  }
}

# IAM role for the EBS CSI controller, trusted by EKS Pod Identity.
data "aws_iam_policy_document" "ebs_csi_assume" {
  statement {
    actions = ["sts:AssumeRole", "sts:TagSession"]

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ebs_csi" {
  name               = "${var.cluster_name}-ebs-csi"
  assume_role_policy = data.aws_iam_policy_document.ebs_csi_assume.json
}

resource "aws_iam_role_policy_attachment" "ebs_csi" {
  role       = aws_iam_role.ebs_csi.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}
