variable "environment" {
  description = "Deployment environment (dev | staging | prod)."
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "rds_instance_class" {
  description = "RDS instance class for PostgreSQL."
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_allocated_storage_gb" {
  description = "Allocated storage in GB for RDS."
  type        = number
  default     = 20
}

variable "rds_db_name" {
  description = "Initial PostgreSQL database name."
  type        = string
  default     = "noticedesk"
}

variable "rds_master_username" {
  description = "Master username for RDS PostgreSQL."
  type        = string
  default     = "noticedesk_admin"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 30
}
