terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# IAM Role for QuickSight Admin Console
resource "aws_iam_role" "quicksuite_admin" {
  name = "QuickSuiteAdmin-${data.aws_caller_identity.current.account_id}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "glue.amazonaws.com",
            "cloudformation.amazonaws.com",
            "firehose.amazonaws.com",
            "streams.metrics.cloudwatch.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "quicksuite_admin_policy" {
  name = "Quick-Suite-Admin-${data.aws_caller_identity.current.account_id}"
  role = aws_iam_role.quicksuite_admin.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iam:Get*",
          "iam:List*",
          "iam:Create*",
          "iam:Update*",
          "iam:PassRole",
          "quicksight:*",
          "glue:*",
          "s3:*",
          "sts:AssumeRole",
          "cloudwatch:*",
          "logs:*",
          "firehose:PutRecord",
          "firehose:PutRecordBatch"
        ]
        Resource = "*"
      }
    ]
  })
}

# S3 Bucket (consolidated)
resource "aws_s3_bucket" "admin_suite" {
  bucket = "admin-suite-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "admin_suite" {
  bucket = aws_s3_bucket.admin_suite.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}