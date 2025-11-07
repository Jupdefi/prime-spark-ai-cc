# RDS Module Outputs

output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "db_instance_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.main.arn
}

output "db_instance_endpoint" {
  description = "RDS instance connection endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_instance_address" {
  description = "RDS instance hostname"
  value       = aws_db_instance.main.address
}

output "db_instance_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "db_instance_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "db_security_group_id" {
  description = "Security group ID attached to RDS"
  value       = aws_security_group.rds.id
}

output "replica_endpoints" {
  description = "Connection endpoints for read replicas"
  value       = aws_db_instance.replica[*].endpoint
}

output "replica_ids" {
  description = "IDs of read replicas"
  value       = aws_db_instance.replica[*].id
}
