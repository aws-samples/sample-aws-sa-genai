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
resource "aws_iam_role" "quicksight_admin_console_2025" {
  name = "QuickSightAdminConsole2025"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "glue.amazonaws.com",
            "cloudformation.amazonaws.com",
            "firehose.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "quicksight_admin_console_policy" {
  name = "QuickSight-AdminConsole-2025"
  role = aws_iam_role.quicksight_admin_console_2025.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iam:*",
          "quicksight:*",
          "glue:*",
          "s3:*",
          "sts:AssumeRole",
          "cloudwatch:*",
          "logs:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# S3 Buckets
resource "aws_s3_bucket" "admin_console_new" {
  bucket = "admin-console-new-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "admin_console_new" {
  bucket = aws_s3_bucket.admin_console_new.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudWatch Metrics S3 Buckets
resource "aws_s3_bucket" "cw_qs_ds" {
  bucket = "cw-qs-ds-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "cw_qs_ds" {
  bucket = aws_s3_bucket.cw_qs_ds.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "cw_qs_ds" {
  bucket = aws_s3_bucket.cw_qs_ds.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cw_qs_ds" {
  bucket = aws_s3_bucket.cw_qs_ds.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket" "cw_qs_dash_visual" {
  bucket = "cw-qs-dash-visual-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "cw_qs_dash_visual" {
  bucket = aws_s3_bucket.cw_qs_dash_visual.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "cw_qs_dash_visual" {
  bucket = aws_s3_bucket.cw_qs_dash_visual.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cw_qs_dash_visual" {
  bucket = aws_s3_bucket.cw_qs_dash_visual.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket" "cw_qs_spice" {
  bucket = "cw-qs-spice-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "cw_qs_spice" {
  bucket = aws_s3_bucket.cw_qs_spice.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "cw_qs_spice" {
  bucket = aws_s3_bucket.cw_qs_spice.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cw_qs_spice" {
  bucket = aws_s3_bucket.cw_qs_spice.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket" "cw_qs_qindex" {
  bucket = "cw-qs-qindex-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "cw_qs_qindex" {
  bucket = aws_s3_bucket.cw_qs_qindex.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "cw_qs_qindex" {
  bucket = aws_s3_bucket.cw_qs_qindex.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cw_qs_qindex" {
  bucket = aws_s3_bucket.cw_qs_qindex.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket" "cw_qs_qaction" {
  bucket = "cw-qs-qaction-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "cw_qs_qaction" {
  bucket = aws_s3_bucket.cw_qs_qaction.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "cw_qs_qaction" {
  bucket = aws_s3_bucket.cw_qs_qaction.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cw_qs_qaction" {
  bucket = aws_s3_bucket.cw_qs_qaction.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}