# Quick Admin Suite

## Data Collection
ETL jobs that collect QuickSight metadata and store in S3 for analysis:
- **admin_suite_user_info_access_manage**: Collects user and group access information
- **admin_suite_data_dictionary**: Gathers dataset and dashboard metadata
- **admin_suite_folder_info**: Extracts folder structure and permissions
- **admin_suite_q_topic_info**: Collects QuickSight Q topics information
- **admin_suite_q_access_info**: Gathers Q object access permissions
- **admin_suite_ds_property**: Collects dataset properties and metadata
- **admin_suite_datasource_property**: Maps datasets to their underlying data sources for dependency tracking

## Data Model
CloudFormation template for AWS Glue database, tables, crawlers, and Athena views supporting QuickSight administration and monitoring.

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

### Crawlers
- **cloudtrail_logs_crawler**: Initial CloudTrail schema discovery
- **cloudtrail_logs_partition_crawler**: CloudTrail partition management
- **cw_qs_ds_crawler**: CloudWatch dataset metrics crawler
- **cw_qs_dash_visual_crawler**: CloudWatch dashboard/visual metrics crawler

### Athena Views (Named Queries)
- **quicksight_crud_events_view**: QuickSight CRUD operations from CloudTrail
- **quicksight_querydb_events_view**: QuickSight database query events
- **qs_usage_cur_vw**: QuickSight usage and cost analysis from CUR data
- **cw_qs_ds_pivot_view**: Pivoted CloudWatch dataset metrics
- **cw_qs_dash_visual_pivot_view**: Pivoted CloudWatch dashboard/visual metrics

## Parameters
- **CloudtrailLocation**: S3 location of CloudTrail logs
- **StartDateParameter**: Start date for CloudTrail data (YYYY/MM/DD)
- **CURSourceTable**: CUR database and table name (format: database.table_name)

## Recent Changes
- Renamed all Glue jobs from legacy names to standardized ETL naming convention
- Updated database name from `adminconsoledb2025` to `admin-console-2025`
- Changed S3 bucket references from `adminconsolenew` to `admin-console-new`
- Added CloudWatch metrics tables and crawlers with proper dependencies
- Integrated CUR analysis with parameterized table reference
- Created Athena named queries for view generation instead of Lambda custom resources
- Added partition management crawlers for CloudTrail and CloudWatch metrics