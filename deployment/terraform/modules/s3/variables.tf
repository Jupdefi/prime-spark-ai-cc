variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "bucket_suffix" {
  type = string
}

variable "versioning_enabled" {
  type    = bool
  default = true
}

variable "kms_key_id" {
  type    = string
  default = ""
}

variable "lifecycle_rules" {
  type    = list(any)
  default = []
}

variable "replication_enabled" {
  type    = bool
  default = false
}

variable "replication_role_arn" {
  type    = string
  default = ""
}

variable "replication_destination_bucket_arn" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
