# Main Terraform Variables

# General
variable "project_name" {
  description = "Project name"
  type        = string
  default     = "prime-spark"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "Primary AWS region"
  type        = string
}

variable "aws_secondary_region" {
  description = "Secondary AWS region for DR"
  type        = string
  default     = "us-west-2"
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}

# VPC Configuration
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
}

variable "database_subnet_cidrs" {
  description = "Database subnet CIDR blocks"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT Gateway"
  type        = bool
  default     = false
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

# EKS Configuration
variable "eks_cluster_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.28"
}

variable "eks_node_groups" {
  description = "EKS node group configurations"
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

variable "eks_public_access_cidrs" {
  description = "CIDR blocks allowed to access EKS public endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# RDS Configuration
variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
}

variable "rds_max_allocated_storage" {
  description = "Maximum allocated storage in GB"
  type        = number
}

variable "rds_database_name" {
  description = "Database name"
  type        = string
  default     = "prime_spark"
}

variable "rds_master_username" {
  description = "Master username"
  type        = string
  sensitive   = true
}

variable "rds_master_password" {
  description = "Master password"
  type        = string
  sensitive   = true
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ"
  type        = bool
  default     = true
}

variable "rds_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "rds_performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = true
}

variable "rds_read_replica_count" {
  description = "Number of read replicas"
  type        = number
  default     = 0
}

# ElastiCache Configuration
variable "redis_node_type" {
  description = "Redis node type"
  type        = string
}

variable "redis_num_cache_clusters" {
  description = "Number of cache clusters"
  type        = number
  default     = 2
}

variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "redis_automatic_failover" {
  description = "Enable automatic failover"
  type        = bool
  default     = true
}

variable "redis_multi_az" {
  description = "Enable Multi-AZ"
  type        = bool
  default     = true
}

variable "redis_snapshot_retention" {
  description = "Snapshot retention period in days"
  type        = number
  default     = 7
}

# S3 Configuration
variable "s3_lifecycle_rules" {
  description = "S3 lifecycle rules"
  type        = list(any)
  default     = []
}

# CloudWatch Configuration
variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}
