# Main Terraform Configuration - Prime Spark AI Infrastructure

# KMS Key for encryption
resource "aws_kms_key" "main" {
  description             = "${var.project_name} encryption key for ${var.environment}"
  deletion_window_in_days = var.environment == "production" ? 30 : 7
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-kms-${var.environment}"
  }
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.project_name}-${var.environment}"
  target_key_id = aws_kms_key.main.key_id
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name     = var.project_name
  environment      = var.environment
  region           = var.aws_region
  vpc_cidr         = var.vpc_cidr
  availability_zones = var.availability_zones

  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs

  enable_nat_gateway   = var.enable_nat_gateway
  single_nat_gateway   = var.single_nat_gateway
  enable_flow_logs     = var.enable_vpc_flow_logs
  enable_s3_endpoint   = true
  enable_ecr_endpoint  = var.environment == "production"

  tags = var.common_tags
}

# EKS Module
module "eks" {
  source = "./modules/eks"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids

  cluster_version = var.eks_cluster_version
  kms_key_arn     = aws_kms_key.main.arn
  node_groups     = var.eks_node_groups

  endpoint_private_access = true
  endpoint_public_access  = var.environment != "production"
  public_access_cidrs     = var.eks_public_access_cidrs

  enable_vpc_cni_addon      = true
  enable_coredns_addon      = true
  enable_kube_proxy_addon   = true
  enable_ebs_csi_addon      = true

  tags = var.common_tags

  depends_on = [module.vpc]
}

# RDS PostgreSQL Module
module "rds" {
  source = "./modules/rds"

  project_name         = var.project_name
  environment          = var.environment
  vpc_id               = module.vpc.vpc_id
  database_subnet_ids  = module.vpc.database_subnet_ids
  allowed_cidr_blocks  = var.private_subnet_cidrs

  engine_version        = var.rds_engine_version
  instance_class        = var.rds_instance_class
  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage

  database_name     = var.rds_database_name
  master_username   = var.rds_master_username
  master_password   = var.rds_master_password
  kms_key_id        = aws_kms_key.main.arn

  multi_az                    = var.rds_multi_az
  backup_retention_period     = var.rds_backup_retention_period
  deletion_protection         = var.environment == "production"
  skip_final_snapshot         = var.environment != "production"
  performance_insights_enabled = var.rds_performance_insights_enabled
  read_replica_count          = var.rds_read_replica_count

  tags = var.common_tags

  depends_on = [module.vpc]
}

# ElastiCache Redis Module
module "elasticache" {
  source = "./modules/elasticache"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  allowed_cidr_blocks = var.private_subnet_cidrs

  node_type            = var.redis_node_type
  num_cache_clusters   = var.redis_num_cache_clusters
  engine_version       = var.redis_engine_version

  automatic_failover_enabled = var.redis_automatic_failover
  multi_az_enabled           = var.redis_multi_az
  snapshot_retention_limit   = var.redis_snapshot_retention

  tags = var.common_tags

  depends_on = [module.vpc]
}

# S3 Buckets Module
module "s3_data" {
  source = "./modules/s3"

  project_name      = var.project_name
  environment       = var.environment
  bucket_suffix     = "data"
  versioning_enabled = true
  kms_key_id        = aws_kms_key.main.arn

  lifecycle_rules = var.s3_lifecycle_rules

  tags = var.common_tags
}

module "s3_backup" {
  source = "./modules/s3"

  project_name       = var.project_name
  environment        = var.environment
  bucket_suffix      = "backup"
  versioning_enabled = true
  kms_key_id         = aws_kms_key.main.arn

  tags = var.common_tags
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/${var.project_name}/${var.environment}/application"
  retention_in_days = var.cloudwatch_log_retention_days
  kms_key_id        = aws_kms_key.main.arn

  tags = var.common_tags
}

resource "aws_cloudwatch_log_group" "infrastructure" {
  name              = "/aws/${var.project_name}/${var.environment}/infrastructure"
  retention_in_days = var.cloudwatch_log_retention_days
  kms_key_id        = aws_kms_key.main.arn

  tags = var.common_tags
}
