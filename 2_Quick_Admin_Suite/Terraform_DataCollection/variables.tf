variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "script_bucket_name" {
  description = "S3 bucket name containing Glue job scripts"
  type        = string
  default     = "admin-console-cfn-dataprepare-code"
}