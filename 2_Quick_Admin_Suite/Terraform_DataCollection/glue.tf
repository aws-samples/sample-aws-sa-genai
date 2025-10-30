# Glue Jobs
resource "aws_glue_job" "etl_job_admin_suite_assets_access" {
  name     = "etl_job_admin_suite_assets_access"
  role_arn = aws_iam_role.quicksight_admin_console_2025.arn

  command {
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoleuserdataaccessinfo.py"
  }

  default_arguments = {
    "--AWS_REGION" = data.aws_region.current.name
  }

  glue_version          = "3.0"
  max_capacity          = 1
  max_retries           = 0
  timeout               = 120
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_console_new]
}

resource "aws_glue_job" "etl_job_admin_suite_assets_metadata" {
  name     = "etl_job_admin_suite_assets_metadata"
  role_arn = aws_iam_role.quicksight_admin_console_2025.arn

  command {
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoledatasetdashboardinfo.py"
  }

  default_arguments = {
    "--AWS_REGION" = data.aws_region.current.name
  }

  glue_version          = "3.0"
  max_capacity          = 1
  max_retries           = 0
  timeout               = 120
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_console_new]
}

resource "aws_glue_job" "etl_job_admin_suite_folder_assets" {
  name     = "etl_job_admin_suite_folder_assets"
  role_arn = aws_iam_role.quicksight_admin_console_2025.arn

  command {
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsolefolderinfo.py"
  }

  default_arguments = {
    "--AWS_REGION" = data.aws_region.current.name
  }

  glue_version          = "3.0"
  max_capacity          = 1
  max_retries           = 0
  timeout               = 120
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_console_new]
}

resource "aws_glue_job" "etl_job_admin_suite_q_access" {
  name     = "etl_job_admin_suite_q_access"
  role_arn = aws_iam_role.quicksight_admin_console_2025.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoleqobjectaccessinfo.py"
  }

  default_arguments = {
    "--region"         = data.aws_region.current.name
    "--aws_account_id" = data.aws_caller_identity.current.account_id
    "--output_s3_path" = "s3://admin-console-new-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/q_object_access"
  }

  glue_version    = "5.0"
  max_retries     = 0
  timeout         = 120
  worker_type     = "G.1X"
  number_of_workers = 2
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_console_new]
}

resource "aws_glue_job" "etl_job_admin_suite_q_metadata" {
  name     = "etl_job_admin_suite_q_metadata"
  role_arn = aws_iam_role.quicksight_admin_console_2025.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoleqtopicinfo.py"
  }

  default_arguments = {
    "--AWS_REGION"     = data.aws_region.current.name
    "--AWS_ACCOUNT_ID" = data.aws_caller_identity.current.account_id
    "--S3_OUTPUT_PATH" = "s3://admin-console-new-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/q_topics_info"
  }

  glue_version    = "5.0"
  max_retries     = 0
  timeout         = 120
  worker_type     = "G.1X"
  number_of_workers = 2
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_console_new]
}

resource "aws_glue_job" "etl_job_admin_suite_ds_properties" {
  name     = "etl_job_admin_suite_ds_properties"
  role_arn = aws_iam_role.quicksight_admin_console_2025.arn

  command {
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/admin_suite_ds_property.py"
  }

  default_arguments = {
    "--AWS_REGION" = data.aws_region.current.name
  }

  glue_version          = "3.0"
  max_capacity          = 1
  max_retries           = 0
  timeout               = 120
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_console_new]
}

resource "aws_glue_job" "etl_job_admin_suite_datasource_properties" {
  name     = "etl_job_admin_suite_datasource_properties"
  role_arn = aws_iam_role.quicksight_admin_console_2025.arn

  command {
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/admin_suite_datasource_property.py"
  }

  default_arguments = {
    "--AWS_REGION"                = data.aws_region.current.name
    "--QUICKSIGHT_IDENTITY_REGION" = data.aws_region.current.name
  }

  glue_version          = "3.0"
  max_capacity          = 1
  max_retries           = 0
  timeout               = 120
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_bucket.admin_console_new]
}

# Glue Triggers (Scheduled)
resource "aws_glue_trigger" "etl_job_admin_suite_assets_access_schedule" {
  name         = "etl-job-admin-suite-assets-access-every-3-hour"
  description  = "Glue Trigger to run etl_job_admin_suite_assets_access glue job every 3 hours"
  type         = "SCHEDULED"
  schedule     = "cron(0 */3 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.etl_job_admin_suite_assets_access.name
  }
}

resource "aws_glue_trigger" "etl_job_admin_suite_assets_metadata_schedule" {
  name         = "etl-job-admin-suite-assets-metadata-every-3-hour"
  description  = "Glue Trigger to run etl_job_admin_suite_assets_metadata glue job every 3 hours"
  type         = "SCHEDULED"
  schedule     = "cron(0 */3 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.etl_job_admin_suite_assets_metadata.name
  }
}

resource "aws_glue_trigger" "etl_job_admin_suite_folder_assets_schedule" {
  name         = "etl-job-admin-suite-folder-assets-every-3-hour"
  description  = "Glue Trigger to run etl_job_admin_suite_folder_assets job every 3 hours"
  type         = "SCHEDULED"
  schedule     = "cron(0 */3 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.etl_job_admin_suite_folder_assets.name
  }
}

resource "aws_glue_trigger" "etl_job_admin_suite_q_metadata_schedule" {
  name         = "etl-job-admin-suite-q-metadata-every-3-hour"
  description  = "Glue Trigger to run etl_job_admin_suite_q_metadata glue job every 3 hours"
  type         = "SCHEDULED"
  schedule     = "cron(0 */3 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.etl_job_admin_suite_q_metadata.name
  }
}

resource "aws_glue_trigger" "etl_job_admin_suite_q_access_schedule" {
  name         = "etl-job-admin-suite-q-access-every-3-hour"
  description  = "Glue Trigger to run etl_job_admin_suite_q_access glue job every 3 hours"
  type         = "SCHEDULED"
  schedule     = "cron(0 */3 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.etl_job_admin_suite_q_access.name
  }
}

resource "aws_glue_trigger" "etl_job_admin_suite_ds_properties_schedule" {
  name         = "etl-job-admin-suite-ds-properties-every-3-hour"
  description  = "Glue Trigger to run etl_job_admin_suite_ds_properties glue job every 3 hours"
  type         = "SCHEDULED"
  schedule     = "cron(0 */3 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.etl_job_admin_suite_ds_properties.name
  }
}

resource "aws_glue_trigger" "etl_job_admin_suite_datasource_properties_schedule" {
  name         = "etl-job-admin-suite-datasource-properties-every-3-hour"
  description  = "Glue Trigger to run etl_job_admin_suite_datasource_properties glue job every 3 hours"
  type         = "SCHEDULED"
  schedule     = "cron(0 */3 * * ? *)"
  start_on_creation = true

  actions {
    job_name = aws_glue_job.etl_job_admin_suite_datasource_properties.name
  }
}