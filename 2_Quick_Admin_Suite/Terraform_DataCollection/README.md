# QuickSight Admin Suite Data Collection - Terraform

This Terraform configuration creates the data collection infrastructure for the QuickSight Admin Suite, including Glue jobs, S3 buckets, and CloudWatch metric streams.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured
- Appropriate AWS permissions

## Usage

1. Initialize Terraform:
```bash
terraform init
```

2. Plan the deployment:
```bash
terraform plan
```

3. Apply the configuration:
```bash
terraform apply
```

## Resources Created

### IAM Roles
- `QuickSightAdminConsole2025`: Main service role for Glue jobs
- `QuickSuiteCWStreamRole`: Role for CloudWatch metric streams

### S3 Buckets
- `admin-console-new-{account-id}`: Main data storage bucket
- `cw-qs-ds-{account-id}`: CloudWatch dataset metrics
- `cw-qs-dash-visual-{account-id}`: Dashboard/visual metrics
- `cw-qs-spice-{account-id}`: SPICE metrics
- `cw-qs-qindex-{account-id}`: Q Index metrics
- `cw-qs-qaction-{account-id}`: Q Action metrics

### Glue Jobs
- `etl_job_admin_suite_assets_access`: User and access data collection
- `etl_job_admin_suite_assets_metadata`: Dataset and dashboard metadata
- `etl_job_admin_suite_folder_assets`: Folder information
- `etl_job_admin_suite_q_access`: Q object access permissions
- `etl_job_admin_suite_q_metadata`: Q topics metadata
- `etl_job_admin_suite_ds_properties`: Dataset properties
- `etl_job_admin_suite_datasource_properties`: Datasource properties

### Scheduled Triggers
All Glue jobs are scheduled to run every 3 hours using cron expressions.

### CloudWatch Infrastructure
- Kinesis Firehose delivery streams for each metric type
- CloudWatch metric streams for QuickSight monitoring

## Cleanup

To destroy all resources:
```bash
terraform destroy
```