# QuickSight Admin Suite Data Model - Terraform

This Terraform configuration creates the data model infrastructure for the QuickSight Admin Suite, including Glue tables, Athena views, and crawlers for data analysis.

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
terraform plan -var="cloudtrail_location=s3://your-cloudtrail-bucket/AWSLogs/123456789123/CloudTrail/" -var="start_date_parameter=2024/01/01" -var="cur_source_table=billing.cur"
```

3. Apply the configuration:
```bash
terraform apply -var="cloudtrail_location=s3://your-cloudtrail-bucket/AWSLogs/123456789123/CloudTrail/" -var="start_date_parameter=2024/01/01" -var="cur_source_table=billing.cur"
```

## Variables

- `cloudtrail_location`: S3 location of your CloudTrail logs
- `start_date_parameter`: Start date for CloudTrail data in YYYY/MM/DD format
- `cur_source_table`: CUR database and table name (format: database.table_name)

## Resources Created

### Glue Database
- `admin-console-2025`: Main database for all tables

### Glue Tables
- `group_membership`: User and group information
- `object_access`: Object access permissions
- `datasets_properties`: Dataset properties and metrics
- `datasource_property`: Dataset to datasource mapping
- CloudWatch metrics tables for QuickSight monitoring

### Athena Views
- `quicksight_crud_events_view`: CRUD operations from CloudTrail
- `quicksight_querydb_events_view`: Query database events
- `qs_usage_cur_vw`: Cost and usage analysis
- `cw_qs_ds_pivot_view`: CloudWatch dataset metrics pivot

### Glue Crawlers
- Various crawlers for CloudWatch metrics data
- Scheduled crawlers for partition management

## Cleanup

To remove all resources:
```bash
terraform destroy
```