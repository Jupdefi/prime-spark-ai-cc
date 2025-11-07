# Main Terraform Outputs

# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

# EKS Outputs
output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "eks_oidc_provider_arn" {
  description = "EKS OIDC provider ARN for IRSA"
  value       = module.eks.oidc_provider_arn
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS connection endpoint"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.db_instance_name
}

# ElastiCache Outputs
output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = module.elasticache.redis_endpoint
  sensitive   = true
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint"
  value       = module.elasticache.redis_reader_endpoint
  sensitive   = true
}

# S3 Outputs
output "s3_data_bucket" {
  description = "S3 data bucket name"
  value       = module.s3_data.bucket_id
}

output "s3_backup_bucket" {
  description = "S3 backup bucket name"
  value       = module.s3_backup.bucket_id
}

# KMS Outputs
output "kms_key_id" {
  description = "KMS key ID"
  value       = aws_kms_key.main.key_id
}

output "kms_key_arn" {
  description = "KMS key ARN"
  value       = aws_kms_key.main.arn
}

# CloudWatch Outputs
output "application_log_group" {
  description = "Application CloudWatch log group"
  value       = aws_cloudwatch_log_group.application.name
}

output "infrastructure_log_group" {
  description = "Infrastructure CloudWatch log group"
  value       = aws_cloudwatch_log_group.infrastructure.name
}
