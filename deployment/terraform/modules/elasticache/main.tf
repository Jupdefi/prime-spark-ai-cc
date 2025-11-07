# ElastiCache Module - Redis Cluster
# Creates ElastiCache Redis with automatic failover

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-redis-subnet-${var.environment}"
  subnet_ids = var.subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-redis-subnet-${var.environment}"
    }
  )
}

resource "aws_security_group" "redis" {
  name        = "${var.project_name}-redis-sg-${var.environment}"
  description = "Security group for ElastiCache Redis"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
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
      Name = "${var.project_name}-redis-sg-${var.environment}"
    }
  )
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.project_name}-redis-${var.environment}"
  replication_group_description = "Redis cluster for ${var.project_name} ${var.environment}"

  engine               = "redis"
  engine_version       = var.engine_version
  node_type            = var.node_type
  num_cache_clusters   = var.num_cache_clusters
  parameter_group_name = aws_elasticache_parameter_group.main.name
  port                 = 6379

  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  automatic_failover_enabled = var.automatic_failover_enabled
  multi_az_enabled           = var.multi_az_enabled

  at_rest_encryption_enabled = true
  transit_encryption_enabled = false  # Set to true if required

  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window          = var.snapshot_window
  maintenance_window       = var.maintenance_window

  notification_topic_arn = var.sns_topic_arn

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-redis-${var.environment}"
    }
  )
}

resource "aws_elasticache_parameter_group" "main" {
  name   = "${var.project_name}-redis-params-${var.environment}"
  family = "redis${var.parameter_group_family}"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  tags = var.tags
}
