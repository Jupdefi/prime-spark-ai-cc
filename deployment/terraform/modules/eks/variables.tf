# EKS Module Variables

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where EKS cluster will be created"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for EKS nodes"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for EKS load balancers"
  type        = list(string)
}

variable "cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "endpoint_private_access" {
  description = "Enable private API server endpoint"
  type        = bool
  default     = true
}

variable "endpoint_public_access" {
  description = "Enable public API server endpoint"
  type        = bool
  default     = true
}

variable "public_access_cidrs" {
  description = "List of CIDR blocks allowed to access public endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enabled_cluster_log_types" {
  description = "List of control plane logging types to enable"
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
}

variable "kms_key_arn" {
  description = "ARN of KMS key for secrets encryption"
  type        = string
}

variable "node_groups" {
  description = "List of EKS node group configurations"
  type = list(object({
    name           = string
    instance_type  = string
    min_nodes      = number
    max_nodes      = number
    desired_nodes  = number
    spot_enabled   = optional(bool, false)
    gpu_enabled    = optional(bool, false)
  }))
}

variable "enable_vpc_cni_addon" {
  description = "Enable VPC CNI addon"
  type        = bool
  default     = true
}

variable "vpc_cni_version" {
  description = "Version of VPC CNI addon"
  type        = string
  default     = "v1.16.0-eksbuild.1"
}

variable "enable_coredns_addon" {
  description = "Enable CoreDNS addon"
  type        = bool
  default     = true
}

variable "coredns_version" {
  description = "Version of CoreDNS addon"
  type        = string
  default     = "v1.10.1-eksbuild.6"
}

variable "enable_kube_proxy_addon" {
  description = "Enable kube-proxy addon"
  type        = bool
  default     = true
}

variable "kube_proxy_version" {
  description = "Version of kube-proxy addon"
  type        = string
  default     = "v1.28.4-eksbuild.1"
}

variable "enable_ebs_csi_addon" {
  description = "Enable EBS CSI driver addon"
  type        = bool
  default     = true
}

variable "ebs_csi_version" {
  description = "Version of EBS CSI driver addon"
  type        = string
  default     = "v1.26.1-eksbuild.1"
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
