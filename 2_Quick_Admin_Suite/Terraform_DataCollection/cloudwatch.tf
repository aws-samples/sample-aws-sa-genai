# IAM Role for CloudWatch Metric Streams
resource "aws_iam_role" "quicksuite_cw_stream_role" {
  name = "QuickSuiteCWStreamRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "streams.metrics.cloudwatch.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "firehose_delivery_policy" {
  name = "FirehoseDeliveryPolicy"
  role = aws_iam_role.quicksuite_cw_stream_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "firehose:PutRecord",
          "firehose:PutRecordBatch"
        ]
        Resource = "*"
      }
    ]
  })
}

# Kinesis Firehose Delivery Streams
resource "aws_kinesis_firehose_delivery_stream" "cw_qs_ds" {
  name        = "MetricStreams-cw-qs-ds-${data.aws_caller_identity.current.account_id}"
  destination = "s3"

  s3_configuration {
    role_arn   = aws_iam_role.quicksight_admin_console_2025.arn
    bucket_arn = aws_s3_bucket.cw_qs_ds.arn
  }

  depends_on = [aws_iam_role.quicksight_admin_console_2025]
}

resource "aws_kinesis_firehose_delivery_stream" "cw_qs_dash_visual" {
  name        = "MetricStreams-cw-qs-dash-visual-${data.aws_caller_identity.current.account_id}"
  destination = "s3"

  s3_configuration {
    role_arn   = aws_iam_role.quicksight_admin_console_2025.arn
    bucket_arn = aws_s3_bucket.cw_qs_dash_visual.arn
  }

  depends_on = [aws_iam_role.quicksight_admin_console_2025]
}

resource "aws_kinesis_firehose_delivery_stream" "cw_qs_spice" {
  name        = "MetricStreams-cw-qs-spice-${data.aws_caller_identity.current.account_id}"
  destination = "s3"

  s3_configuration {
    role_arn   = aws_iam_role.quicksight_admin_console_2025.arn
    bucket_arn = aws_s3_bucket.cw_qs_spice.arn
  }

  depends_on = [
    aws_iam_role.quicksight_admin_console_2025,
    aws_s3_bucket.cw_qs_spice
  ]
}

resource "aws_kinesis_firehose_delivery_stream" "cw_qs_qindex" {
  name        = "MetricStreams-cw-qs-qindex-${data.aws_caller_identity.current.account_id}"
  destination = "s3"

  s3_configuration {
    role_arn   = aws_iam_role.quicksight_admin_console_2025.arn
    bucket_arn = aws_s3_bucket.cw_qs_qindex.arn
  }

  depends_on = [
    aws_iam_role.quicksight_admin_console_2025,
    aws_s3_bucket.cw_qs_qindex
  ]
}

resource "aws_kinesis_firehose_delivery_stream" "cw_qs_qaction" {
  name        = "MetricStreams-cw-qs-qaction-${data.aws_caller_identity.current.account_id}"
  destination = "s3"

  s3_configuration {
    role_arn   = aws_iam_role.quicksight_admin_console_2025.arn
    bucket_arn = aws_s3_bucket.cw_qs_qaction.arn
  }

  depends_on = [
    aws_iam_role.quicksight_admin_console_2025,
    aws_s3_bucket.cw_qs_qaction
  ]
}

# CloudWatch Metric Streams
resource "aws_cloudwatch_metric_stream" "ds" {
  name          = "cw-qs-ds"
  firehose_arn  = aws_kinesis_firehose_delivery_stream.cw_qs_ds.arn
  role_arn      = aws_iam_role.quicksuite_cw_stream_role.arn
  output_format = "json"

  include_filter {
    namespace    = "AWS/QuickSight"
    metric_names = [
      "IngestionRowCount",
      "IngestionLatency",
      "IngestionInvocationCount",
      "IngestionErrorCount"
    ]
  }
}

resource "aws_cloudwatch_metric_stream" "dash_visual" {
  name          = "cw-qs-dash-visual"
  firehose_arn  = aws_kinesis_firehose_delivery_stream.cw_qs_dash_visual.arn
  role_arn      = aws_iam_role.quicksuite_cw_stream_role.arn
  output_format = "json"

  include_filter {
    namespace    = "AWS/QuickSight"
    metric_names = [
      "VisualLoadTime",
      "DashboardViewLoadTime",
      "DashboardViewCount",
      "VisualLoadErrorCount"
    ]
  }
}

resource "aws_cloudwatch_metric_stream" "spice" {
  name          = "cw-qs-spice"
  firehose_arn  = aws_kinesis_firehose_delivery_stream.cw_qs_spice.arn
  role_arn      = aws_iam_role.quicksuite_cw_stream_role.arn
  output_format = "json"

  include_filter {
    namespace    = "AWS/QuickSight"
    metric_names = [
      "SPICECapacityLimitInMB",
      "SPICECapacityConsumedInMB"
    ]
  }
}

resource "aws_cloudwatch_metric_stream" "qindex" {
  name          = "cw-qs-qindex"
  firehose_arn  = aws_kinesis_firehose_delivery_stream.cw_qs_qindex.arn
  role_arn      = aws_iam_role.quicksuite_cw_stream_role.arn
  output_format = "json"

  include_filter {
    namespace    = "AWS/QuickSight"
    metric_names = [
      "QuickIndexDocumentCount",
      "QuickIndexExtractedTextSize"
    ]
  }
}

resource "aws_cloudwatch_metric_stream" "qaction" {
  name          = "cw-qs-qaction"
  firehose_arn  = aws_kinesis_firehose_delivery_stream.cw_qs_qaction.arn
  role_arn      = aws_iam_role.quicksuite_cw_stream_role.arn
  output_format = "json"

  include_filter {
    namespace    = "AWS/QuickSight"
    metric_names = [
      "ActionInvocationError",
      "ActionInvocationCount"
    ]
  }
}