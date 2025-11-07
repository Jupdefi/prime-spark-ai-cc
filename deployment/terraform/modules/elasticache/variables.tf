variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "allowed_cidr_blocks" {
  type = list(string)
}

variable "node_type" {
  type    = string
  default = "cache.r6g.large"
}

variable "num_cache_clusters" {
  type    = number
  default = 2
}

variable "engine_version" {
  type    = string
  default = "7.0"
}

variable "parameter_group_family" {
  type    = string
  default = "7"
}

variable "automatic_failover_enabled" {
  type    = bool
  default = true
}

variable "multi_az_enabled" {
  type    = bool
  default = true
}

variable "snapshot_retention_limit" {
  type    = number
  default = 7
}

variable "snapshot_window" {
  type    = string
  default = "03:00-05:00"
}

variable "maintenance_window" {
  type    = string
  default = "mon:05:00-mon:07:00"
}

variable "sns_topic_arn" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
