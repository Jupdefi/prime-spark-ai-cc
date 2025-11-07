# S3 Module - Object Storage with Versioning and Lifecycle

resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-${var.bucket_suffix}-${var.environment}"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.bucket_suffix}-${var.environment}"
    }
  )
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != "" ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id != "" ? var.kms_key_id : null
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "main" {
  count  = length(var.lifecycle_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.main.id

  dynamic "rule" {
    for_each = var.lifecycle_rules

    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      dynamic "transition" {
        for_each = lookup(rule.value, "transitions", [])

        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = lookup(rule.value, "expiration_days", null) != null ? [1] : []

        content {
          days = rule.value.expiration_days
        }
      }
    }
  }
}

resource "aws_s3_bucket_replication_configuration" "main" {
  count = var.replication_enabled ? 1 : 0

  depends_on = [aws_s3_bucket_versioning.main]
  bucket     = aws_s3_bucket.main.id
  role       = var.replication_role_arn

  rule {
    id     = "replicate-all"
    status = "Enabled"

    destination {
      bucket        = var.replication_destination_bucket_arn
      storage_class = "STANDARD_IA"
    }
  }
}
