# EKS Module - Kubernetes Cluster on AWS
# Creates EKS cluster with managed node groups and auto-scaling

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = "${var.project_name}-eks-${var.environment}"
  role_arn = aws_iam_role.cluster.arn
  version  = var.cluster_version

  vpc_config {
    subnet_ids              = concat(var.private_subnet_ids, var.public_subnet_ids)
    endpoint_private_access = var.endpoint_private_access
    endpoint_public_access  = var.endpoint_public_access
    public_access_cidrs     = var.public_access_cidrs
    security_group_ids      = [aws_security_group.cluster.id]
  }

  enabled_cluster_log_types = var.enabled_cluster_log_types

  encryption_config {
    provider {
      key_arn = var.kms_key_arn
    }
    resources = ["secrets"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-eks-${var.environment}"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.cluster_AmazonEKSClusterPolicy,
    aws_iam_role_policy_attachment.cluster_AmazonEKSVPCResourceController,
  ]
}

# EKS Cluster IAM Role
resource "aws_iam_role" "cluster" {
  name = "${var.project_name}-eks-cluster-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster.name
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSVPCResourceController" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.cluster.name
}

# EKS Cluster Security Group
resource "aws_security_group" "cluster" {
  name        = "${var.project_name}-eks-cluster-sg-${var.environment}"
  description = "Security group for EKS cluster"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-eks-cluster-sg-${var.environment}"
    }
  )
}

# EKS Node Groups
resource "aws_eks_node_group" "main" {
  for_each = { for ng in var.node_groups : ng.name => ng }

  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project_name}-${each.value.name}-${var.environment}"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = [each.value.instance_type]
  capacity_type   = each.value.spot_enabled ? "SPOT" : "ON_DEMAND"

  scaling_config {
    desired_size = each.value.desired_nodes
    max_size     = each.value.max_nodes
    min_size     = each.value.min_nodes
  }

  update_config {
    max_unavailable = 1
  }

  labels = merge(
    {
      "node-group" = each.value.name
      "environment" = var.environment
    },
    lookup(each.value, "gpu_enabled", false) ? { "gpu" = "true" } : {}
  )

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${each.value.name}-${var.environment}"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
  ]
}

# EKS Node Group IAM Role
resource "aws_iam_role" "node_group" {
  name = "${var.project_name}-eks-node-group-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node_group.name
}

# OIDC Provider for IRSA (IAM Roles for Service Accounts)
data "tls_certificate" "cluster" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "cluster" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.cluster.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-eks-oidc-${var.environment}"
    }
  )
}

# EKS Add-ons
resource "aws_eks_addon" "vpc_cni" {
  count             = var.enable_vpc_cni_addon ? 1 : 0
  cluster_name      = aws_eks_cluster.main.name
  addon_name        = "vpc-cni"
  addon_version     = var.vpc_cni_version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = var.tags
}

resource "aws_eks_addon" "coredns" {
  count             = var.enable_coredns_addon ? 1 : 0
  cluster_name      = aws_eks_cluster.main.name
  addon_name        = "coredns"
  addon_version     = var.coredns_version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = var.tags

  depends_on = [
    aws_eks_node_group.main
  ]
}

resource "aws_eks_addon" "kube_proxy" {
  count             = var.enable_kube_proxy_addon ? 1 : 0
  cluster_name      = aws_eks_cluster.main.name
  addon_name        = "kube-proxy"
  addon_version     = var.kube_proxy_version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = var.tags
}

resource "aws_eks_addon" "ebs_csi" {
  count             = var.enable_ebs_csi_addon ? 1 : 0
  cluster_name      = aws_eks_cluster.main.name
  addon_name        = "aws-ebs-csi-driver"
  addon_version     = var.ebs_csi_version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = var.tags

  depends_on = [
    aws_iam_role_policy_attachment.ebs_csi_driver
  ]
}

# IAM Role for EBS CSI Driver
resource "aws_iam_role" "ebs_csi_driver" {
  count = var.enable_ebs_csi_addon ? 1 : 0
  name  = "${var.project_name}-ebs-csi-driver-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.cluster.arn
      }
      Condition = {
        StringEquals = {
          "${replace(aws_iam_openid_connect_provider.cluster.url, "https://", "")}:sub" = "system:serviceaccount:kube-system:ebs-csi-controller-sa"
          "${replace(aws_iam_openid_connect_provider.cluster.url, "https://", "")}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ebs_csi_driver" {
  count      = var.enable_ebs_csi_addon ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
  role       = aws_iam_role.ebs_csi_driver[0].name
}
