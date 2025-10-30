# Glue Crawlers
resource "aws_glue_crawler" "cw_qs_ds" {
  name          = "crawler-cw-qs-ds"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSightAdminConsole2025"
  database_name = aws_glue_catalog_database.admin_console_db.name

  s3_target {
    path = "s3://cw-qs-ds-${data.aws_caller_identity.current.account_id}/"
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
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSightAdminConsole2025"
  database_name = aws_glue_catalog_database.admin_console_db.name

  s3_target {
    path = "s3://cw-qs-spice-${data.aws_caller_identity.current.account_id}/"
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
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSightAdminConsole2025"
  database_name = aws_glue_catalog_database.admin_console_db.name

  s3_target {
    path = "s3://cw-qs-dash-visual-${data.aws_caller_identity.current.account_id}/"
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

# Scheduled Crawlers for Partition Management
resource "aws_glue_crawler" "cw_qs_ds_add_part" {
  name          = "crawler-cw-qs-ds-add-part"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSightAdminConsole2025"
  database_name = aws_glue_catalog_database.admin_console_db.name
  schedule      = "cron(0 * * * ? *)"

  catalog_target {
    database_name = aws_glue_catalog_database.admin_console_db.name
    tables        = [aws_glue_catalog_table.cw_qs_ds.name]
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
  })

  depends_on = [aws_glue_catalog_table.cw_qs_ds]
}

resource "aws_glue_crawler" "cw_qs_spice_add_part" {
  name          = "crawler-cw-qs-spice-add-part"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSightAdminConsole2025"
  database_name = aws_glue_catalog_database.admin_console_db.name
  schedule      = "cron(0 * * * ? *)"

  catalog_target {
    database_name = aws_glue_catalog_database.admin_console_db.name
    tables        = [aws_glue_catalog_table.cw_qs_spice.name]
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
  })

  depends_on = [aws_glue_catalog_table.cw_qs_spice]
}

resource "aws_glue_crawler" "cw_qs_dash_visual_add_part" {
  name          = "crawler-cw-qs-dash-visual-add-part"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/QuickSightAdminConsole2025"
  database_name = aws_glue_catalog_database.admin_console_db.name
  schedule      = "cron(0 * * * ? *)"

  catalog_target {
    database_name = aws_glue_catalog_database.admin_console_db.name
    tables        = [aws_glue_catalog_table.cw_qs_dash_visual.name]
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
  })

  depends_on = [aws_glue_catalog_table.cw_qs_dash_visual]
}