# Glue Crawlers
resource "aws_glue_crawler" "cw_qs_ds" {
  name          = "crawler-cw-qs-ds"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSuiteAdmin-${data.aws_caller_identity.current.account_id}"
  database_name = aws_glue_catalog_database.admin_console_db.name
  schedule      = "cron(0 4 * * ? *)"

  s3_target {
    path = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-ds/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CreatePartitionIndex = true
  })
}

resource "aws_glue_crawler" "cw_qs_spice" {
  name          = "crawler-cw-qs-spice"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSuiteAdmin-${data.aws_caller_identity.current.account_id}"
  database_name = aws_glue_catalog_database.admin_console_db.name
  schedule      = "cron(15 4 * * ? *)"

  s3_target {
    path = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-spice/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CreatePartitionIndex = true
  })
}

resource "aws_glue_crawler" "cw_qs_qindex" {
  name          = "crawler-cw-qs-qindex"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSuiteAdmin-${data.aws_caller_identity.current.account_id}"
  database_name = aws_glue_catalog_database.admin_console_db.name
  schedule      = "cron(30 4 * * ? *)"

  s3_target {
    path = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-qindex/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CreatePartitionIndex = true
  })
}

resource "aws_glue_crawler" "cw_qs_qaction" {
  name          = "crawler-cw-qs-qaction"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSuiteAdmin-${data.aws_caller_identity.current.account_id}"
  database_name = aws_glue_catalog_database.admin_console_db.name
  schedule      = "cron(45 4 * * ? *)"

  s3_target {
    path = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-qaction/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CreatePartitionIndex = true
  })
}

resource "aws_glue_crawler" "cw_qs_dash_visual" {
  name          = "crawler-cw-qs-dash-visual"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSuiteAdmin-${data.aws_caller_identity.current.account_id}"
  database_name = aws_glue_catalog_database.admin_console_db.name
  schedule      = "cron(0 5 * * ? *)"

  s3_target {
    path = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-dash-visual/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CreatePartitionIndex = true
  })
}

# Crawler Trigger Job
resource "aws_glue_job" "crawler_trigger" {
  name     = "crawler-trigger-job"
  role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSuiteAdmin-${data.aws_caller_identity.current.account_id}"

  command {
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://${var.script_bucket_name}/glue/scripts/2025/crawler_trigger.py"
  }

  default_arguments = {
    "--job-language"    = "python"
    "--enable-metrics" = ""
  }

  glue_version = "3.0"
  max_capacity = 0.0625
  max_retries  = 0
  timeout      = 60
}