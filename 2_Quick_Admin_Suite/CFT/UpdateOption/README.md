# Quick Admin Suite

## CloudFormation Templates

### Data Collection (quick_admin_suite_data_collection.template)
ETL jobs, S3 buckets, and CloudWatch metric streams for QuickSight data collection:
- **etl_job_admin_suite_assets_access**: User and group access information
- **etl_job_admin_suite_assets_metadata**: Dataset and dashboard metadata
- **etl_job_admin_suite_folder_assets**: Folder structure and permissions
- **etl_job_admin_suite_q_metadata**: QuickSight Q topics information
- **etl_job_admin_suite_q_access**: Q object access permissions
- **etl_job_admin_suite_ds_properties**: Dataset properties and metadata
- **etl_job_admin_suite_datasource_properties**: Dataset to datasource dependency mapping

### Data Model (quick_admin_suite_data_model.yaml)
Glue database, tables, and crawlers for QuickSight metadata storage.

### Athena Views (quick_admin_suite_athena_views.yaml)
Named queries for analytical views and reporting.

### Key Components

### Database
- **admin-console-2025**: Main Glue database for all QuickSight metadata

### Tables
- **group_membership**: User and group relationships
- **object_access**: Object permissions and access control
- **folder_assets**: Folder asset relationships
- **folder_lk**: Folder permissions lookup
- **folder_path**: Folder hierarchy paths
- **cloudtrail_logs_pp**: Partitioned CloudTrail logs
- **qtopicsinfo**: QuickSight Q topics metadata
- **qobjectaccessinfo**: Q object access permissions
- **datasets_properties**: Dataset properties and metadata
- **datasource_property**: Dataset to datasource dependency mapping
- **cw_qs_ds_[AccountId]**: CloudWatch QuickSight dataset metrics
- **cw_qs_dash_visual_[AccountId]**: CloudWatch dashboard/visual metrics
- **cw_qs_spice_[AccountId]**: CloudWatch SPICE capacity metrics
- **cw_qs_qindex_[AccountId]**: CloudWatch Q Index metrics
- **cw_qs_qaction_[AccountId]**: CloudWatch Q Action metrics

### Crawlers
- **cloudtrail_logs_crawler**: Initial CloudTrail schema discovery
- **cloudtrail_logs_partition_crawler**: CloudTrail partition management
- **cw_qs_ds_crawler**: CloudWatch dataset metrics crawler
- **cw_qs_dash_visual_crawler**: CloudWatch dashboard/visual metrics crawler
- **cw_qs_spice_crawler**: CloudWatch SPICE capacity metrics crawler
- **cw_qs_qindex_crawler**: CloudWatch Q Index metrics crawler
- **cw_qs_qaction_crawler**: CloudWatch Q Action metrics crawler

### Athena Views (Named Queries)
- **quicksight_crud_events_view**: QuickSight CRUD operations from CloudTrail
- **quicksight_querydb_events_view**: QuickSight database query events
- **qs_usage_cur_vw**: QuickSight usage and cost analysis from CUR data
- **cw_qs_ds_pivot_view**: Pivoted CloudWatch dataset metrics
- **cw_qs_dash_visual_pivot_view**: Pivoted CloudWatch dashboard/visual metrics
- **cw_qs_spice_pivot_view**: Pivoted CloudWatch SPICE capacity metrics
- **cw_qs_qindex_pivot_view**: Pivoted CloudWatch Q Index metrics
- **qs_ds_info_combined_view**: Combined dataset properties and info

## Parameters

### Data Collection Template
- No parameters required

### Data Model Template
- **CloudtrailLocation**: S3 location of CloudTrail logs
- **StartDateParameter**: Start date for CloudTrail data (YYYY/MM/DD)

### Athena Views Template
- **CURSourceTable**: CUR database and table name (format: database.table_name)

## Deployment Order
1. **quick_admin_suite_data_collection.template**: Deploy first to create ETL jobs and S3 buckets
2. **quick_admin_suite_data_model.yaml**: Deploy second to create database and tables
3. **quick_admin_suite_athena_views.yaml**: Deploy third to create analytical views

## Infrastructure as Code Alternatives
- **CDK_DataCollection/**: CDK Python version of data collection template
- **CDK_DataModel/**: CDK Python version of data model template
- **Terraform_DataCollection/**: Terraform version of data collection template
- **Terraform_DataModel/**: Terraform version of data model template