variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cur_source_table" {
  description = "Provide CUR database and table name with format database.table_name as it exists in your account (e.g., billing.cur)"
  type        = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+$", var.cur_source_table))
    error_message = "Must be in format database.table_name."
  }
}