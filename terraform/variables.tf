variable "region" {
  description = "AWS region"
  type = string
  default = "us-east-1"
}

variable "access_key" {
  description = "AWS access key"
  type =string
  default = "test"
}

variable "secret_key" {
  description = "secret key"
  type  = string
  default = "test"
}

variable "localstack_endpoint" {
  description = "LocalStack endpoint URL"
  type        = string
  default     = "http://localhost:4566"
}

variable "upload_bucket" {
  description = "S3 bucket name to upload files"
  type = string
  default = "migration_uploads"
}

variable "migration_results" {
  description = "S3 bucket name to upload migrated files"
  type = string
  default = "migration-results"
}

variable "force_destroy" {
  description = "Allow bucket deletion even if it has files. True for local, false for prod."
  type = bool
  default = false
}

variable "is_local" {
  description = "Whether running against LocalStack (true) or AWS (false)"
  type = bool
  default = true
}