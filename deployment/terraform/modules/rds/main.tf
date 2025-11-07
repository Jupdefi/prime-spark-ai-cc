# RDS Module - PostgreSQL Database
# Creates RDS PostgreSQL instance with multi-AZ support and read replicas

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-${var.environment}"
  subnet_ids = var.database_subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-db-subnet-${var.environment}"
    }
  )
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg-${var.environment}"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
    description = "PostgreSQL access from allowed networks"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-rds-sg-${var.environment}"
    }
  )
}

# DB Parameter Group
resource "aws_db_parameter_group" "main" {
  name   = "${var.project_name}-pg-params-${var.environment}"
  family = "postgres${var.engine_version_major}"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = var.environment == "production" ? "ddl" : "all"
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  tags = var.tags
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-db-${var.environment}"
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = var.kms_key_id

  db_name  = var.database_name
  username = var.master_username
  password = var.master_password
  port     = 5432

  multi_az               = var.multi_az
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.main.name

  backup_retention_period   = var.backup_retention_period
  backup_window             = var.backup_window
  maintenance_window        = var.maintenance_window
  copy_tags_to_snapshot     = true
  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.project_name}-db-final-${var.environment}-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_retention_period = var.performance_insights_enabled ? var.performance_insights_retention : null
  performance_insights_kms_key_id       = var.performance_insights_enabled ? var.kms_key_id : null

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-db-${var.environment}"
    }
  )
}

# Read Replicas
resource "aws_db_instance" "replica" {
  count = var.read_replica_count

  identifier          = "${var.project_name}-db-replica-${count.index + 1}-${var.environment}"
  replicate_source_db = aws_db_instance.main.identifier
  instance_class      = var.replica_instance_class != "" ? var.replica_instance_class : var.instance_class

  multi_az                  = false
  vpc_security_group_ids    = [aws_security_group.rds.id]
  backup_retention_period   = 0
  skip_final_snapshot       = true
  deletion_protection       = false
  publicly_accessible       = false
  auto_minor_version_upgrade = true

  performance_insights_enabled = var.performance_insights_enabled

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-db-replica-${count.index + 1}-${var.environment}"
    }
  )
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  count = var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.project_name}-rds-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Database CPU utilization is too high"
  alarm_actions       = var.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "database_memory" {
  count = var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.project_name}-rds-memory-${var.environment}"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeableMemory"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000000000"  # 1GB in bytes
  alarm_description   = "Database freeable memory is too low"
  alarm_actions       = var.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "database_storage" {
  count = var.enable_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.project_name}-rds-storage-${var.environment}"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "10000000000"  # 10GB in bytes
  alarm_description   = "Database free storage space is too low"
  alarm_actions       = var.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}
