variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cloudtrail_location" {
  description = "Enter the location of your trail as specified in the Cloudtrail console, start with s3://, end with CloudTrail/"
  type        = string
  validation {
    condition     = length(var.cloudtrail_location) > 0
    error_message = "CloudTrail location must not be empty."
  }
}

variable "start_date_parameter" {
  description = "Input the start date for the data in the Cloudtrail bucket in YYYY/MM/DD format"
  type        = string
  validation {
    condition     = length(var.start_date_parameter) >= 10
    error_message = "Start date must be at least 10 characters long."
  }
}

variable "script_bucket_name" {
  description = "S3 bucket name containing Glue job scripts"
  type        = string
  default     = "admin-console-cfn-dataprepare-code"
}

