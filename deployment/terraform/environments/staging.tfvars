# Staging Environment Terraform Variables

environment  = "staging"
aws_region   = "us-east-1"
project_name = "prime-spark"

# VPC Configuration
vpc_cidr            = "10.1.0.0/16"
availability_zones  = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnet_cidrs = ["10.1.10.0/24", "10.1.11.0/24"]
database_subnet_cidrs = ["10.1.20.0/24", "10.1.21.0/24"]

enable_nat_gateway = true
single_nat_gateway = true  # Cost optimization for staging
enable_vpc_flow_logs = true

# EKS Configuration
eks_cluster_version = "1.28"
eks_node_groups = [
  {
    name          = "general"
    instance_type = "t3.xlarge"
    min_nodes     = 2
    max_nodes     = 4
    desired_nodes = 2
    spot_enabled  = false
    gpu_enabled   = false
  },
  {
    name          = "ai-workloads"
    instance_type = "g4dn.xlarge"
    min_nodes     = 1
    max_nodes     = 2
    desired_nodes = 1
    spot_enabled  = false
    gpu_enabled   = true
  }
]

# RDS Configuration
rds_instance_class        = "db.t3.large"
rds_allocated_storage     = 100
rds_max_allocated_storage = 500
rds_multi_az              = true
rds_backup_retention_period = 7
rds_performance_insights_enabled = true
rds_read_replica_count    = 0

# ElastiCache Configuration
redis_node_type         = "cache.r6g.large"
redis_num_cache_clusters = 2
redis_engine_version    = "7.0"
redis_automatic_failover = true
redis_multi_az          = false  # Cost optimization
redis_snapshot_retention = 7

# S3 Lifecycle Rules
s3_lifecycle_rules = [
  {
    id      = "transition-to-ia"
    enabled = true
    transitions = [
      {
        days          = 30
        storage_class = "STANDARD_IA"
      },
      {
        days          = 90
        storage_class = "GLACIER"
      }
    ]
  }
]

# CloudWatch Configuration
cloudwatch_log_retention_days = 30

# Common Tags
common_tags = {
  Environment = "staging"
  Project     = "prime-spark-ai"
  ManagedBy   = "terraform"
  CostCenter  = "engineering"
}
