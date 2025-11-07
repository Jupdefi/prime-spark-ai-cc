# Production Environment Terraform Variables

environment         = "production"
aws_region          = "us-east-1"
aws_secondary_region = "us-west-2"
project_name        = "prime-spark"

# VPC Configuration
vpc_cidr            = "10.0.0.0/16"
availability_zones  = ["us-east-1a", "us-east-1b", "us-east-1c"]
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
database_subnet_cidrs = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]

enable_nat_gateway   = true
single_nat_gateway   = false  # High availability
enable_vpc_flow_logs = true

# EKS Configuration
eks_cluster_version = "1.28"
eks_node_groups = [
  {
    name          = "general-purpose"
    instance_type = "m6i.2xlarge"
    min_nodes     = 4
    max_nodes     = 12
    desired_nodes = 6
    spot_enabled  = false
    gpu_enabled   = false
  },
  {
    name          = "ai-inference"
    instance_type = "g5.2xlarge"
    min_nodes     = 2
    max_nodes     = 8
    desired_nodes = 3
    spot_enabled  = false
    gpu_enabled   = true
  },
  {
    name          = "memory-optimized"
    instance_type = "r6i.2xlarge"
    min_nodes     = 2
    max_nodes     = 6
    desired_nodes = 2
    spot_enabled  = false
    gpu_enabled   = false
  },
  {
    name          = "spot-batch"
    instance_type = "c6i.4xlarge"
    min_nodes     = 0
    max_nodes     = 10
    desired_nodes = 0
    spot_enabled  = true
    gpu_enabled   = false
  }
]

# RDS Configuration
rds_instance_class               = "db.r6g.2xlarge"
rds_allocated_storage            = 500
rds_max_allocated_storage        = 2000
rds_multi_az                     = true
rds_backup_retention_period      = 30
rds_performance_insights_enabled = true
rds_read_replica_count           = 2

# ElastiCache Configuration
redis_node_type          = "cache.r6g.2xlarge"
redis_num_cache_clusters = 3
redis_engine_version     = "7.0"
redis_automatic_failover = true
redis_multi_az           = true
redis_snapshot_retention = 7

# S3 Lifecycle Rules
s3_lifecycle_rules = [
  {
    id      = "intelligent-tiering"
    enabled = true
    transitions = [
      {
        days          = 90
        storage_class = "INTELLIGENT_TIERING"
      }
    ]
  }
]

# CloudWatch Configuration
cloudwatch_log_retention_days = 90

# Common Tags
common_tags = {
  Environment = "production"
  Project     = "prime-spark-ai"
  ManagedBy   = "terraform"
  CostCenter  = "production"
  Compliance  = "soc2-iso27001"
  Backup      = "required"
}
