# Glue Jobs
resource "aws_glue_job" "admin_suite_user_info_access_manage" {
  name     = "admin_suite_user_info_access_manage"
  role_arn = aws_iam_role.quicksuite_admin.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.script_bucket_name}/glue/scripts/2025/admin_suite_user_info_access_manage.py"
  }

  default_arguments = {
    "--AWS_REGION"     = data.aws_region.current.name
    "--S3_OUTPUT_PATH" = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/assets_access"
  }

  glue_version      = "5.0"
  max_retries       = 0
  timeout           = 120
  worker_type       = "G.1X"
  number_of_workers = 2
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_suite]
}

resource "aws_glue_job" "admin_suite_dataset" {
  name     = "admin_suite_dataset"
  role_arn = aws_iam_role.quicksuite_admin.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.script_bucket_name}/glue/scripts/2025/admin_suite_dataset.py"
  }

  default_arguments = {
    "--AWS_REGION"     = data.aws_region.current.name
    "--S3_OUTPUT_PATH" = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/dataset"
  }

  glue_version      = "5.0"
  max_retries       = 0
  timeout           = 120
  worker_type       = "G.1X"
  number_of_workers = 2
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_suite]
}

resource "aws_glue_job" "admin_suite_folder" {
  name     = "admin_suite_folder"
  role_arn = aws_iam_role.quicksuite_admin.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.script_bucket_name}/glue/scripts/2025/admin_suite_folder.py"
  }

  default_arguments = {
    "--AWS_REGION"     = data.aws_region.current.name
    "--S3_OUTPUT_PATH" = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/folder_assets"
  }

  glue_version      = "5.0"
  max_retries       = 0
  timeout           = 120
  worker_type       = "G.1X"
  number_of_workers = 2
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_suite]
}

resource "aws_glue_job" "admin_suite_q" {
  name     = "admin_suite_q"
  role_arn = aws_iam_role.quicksuite_admin.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.script_bucket_name}/glue/scripts/2025/admin_suite_q.py"
  }

  default_arguments = {
    "--AWS_REGION"     = data.aws_region.current.name
    "--AWS_ACCOUNT_ID" = data.aws_caller_identity.current.account_id
    "--S3_OUTPUT_PATH" = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/q_md"
  }

  glue_version      = "5.0"
  max_retries       = 0
  timeout           = 120
  worker_type       = "G.1X"
  number_of_workers = 2
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_suite]
}

resource "aws_glue_job" "admin_suite_datasource" {
  name     = "admin_suite_datasource"
  role_arn = aws_iam_role.quicksuite_admin.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.script_bucket_name}/glue/scripts/2025/admin_suite_datasource.py"
  }

  default_arguments = {
    "--AWS_REGION"                 = data.aws_region.current.name
    "--QUICKSIGHT_IDENTITY_REGION" = data.aws_region.current.name
    "--S3_OUTPUT_PATH"             = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/datasource_property"
  }

  glue_version      = "5.0"
  max_retries       = 0
  timeout           = 120
  worker_type       = "G.1X"
  number_of_workers = 2
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_suite]
}

# Glue Triggers (Scheduled)
resource "aws_glue_trigger" "admin_suite_assets_access_schedule" {
  name              = "etl-job-admin-suite-assets-access-daily"
  description       = "Glue Trigger to run admin_suite_user_info_access_manage glue job daily"
  type              = "SCHEDULED"
  schedule          = "cron(0 2 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.admin_suite_user_info_access_manage.name
  }
}

resource "aws_glue_trigger" "admin_suite_assets_metadata_schedule" {
  name              = "etl-job-admin-suite-assets-metadata-daily"
  description       = "Glue Trigger to run admin_suite_dataset glue job daily"
  type              = "SCHEDULED"
  schedule          = "cron(15 2 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.admin_suite_dataset.name
  }
}

resource "aws_glue_trigger" "admin_suite_folder_assets_schedule" {
  name              = "etl-job-admin-suite-folder-assets-daily"
  description       = "Glue Trigger to run admin_suite_folder job daily"
  type              = "SCHEDULED"
  schedule          = "cron(30 2 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.admin_suite_folder.name
  }
}

resource "aws_glue_trigger" "admin_suite_q_metadata_schedule" {
  name              = "etl-job-admin-suite-q-metadata-daily"
  description       = "Glue Trigger to run admin_suite_q glue job daily"
  type              = "SCHEDULED"
  schedule          = "cron(45 2 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.admin_suite_q.name
  }
}

resource "aws_glue_trigger" "admin_suite_datasource_properties_schedule" {
  name              = "etl-job-admin-suite-datasource-properties-daily"
  description       = "Glue Trigger to run admin_suite_datasource glue job daily"
  type              = "SCHEDULED"
  schedule          = "cron(5 3 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.admin_suite_datasource.name
  }
}