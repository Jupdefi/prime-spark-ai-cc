# VPC Module Variables

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT Gateway for all private subnets (cost optimization)"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "flow_logs_role_arn" {
  description = "IAM role ARN for VPC Flow Logs"
  type        = string
  default     = ""
}

variable "flow_logs_destination" {
  description = "Destination for VPC Flow Logs (CloudWatch Log Group ARN or S3 bucket ARN)"
  type        = string
  default     = ""
}

variable "flow_logs_destination_type" {
  description = "Type of flow logs destination (cloud-watch-logs or s3)"
  type        = string
  default     = "cloud-watch-logs"
}

variable "enable_s3_endpoint" {
  description = "Enable S3 VPC Endpoint"
  type        = bool
  default     = true
}

variable "enable_ecr_endpoint" {
  description = "Enable ECR VPC Endpoints"
  type        = bool
  default     = false
}

variable "vpc_endpoint_security_group_id" {
  description = "Security group ID for VPC endpoints"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
