# QuickSight Admin Suite Data Model - CDK Version

This CDK application creates the data model infrastructure for the QuickSight Admin Suite, including Glue database, tables, and crawlers for data storage and discovery.

## Prerequisites

- AWS CDK CLI installed
- Python 3.7 or later
- AWS credentials configured

## Installation

1. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Deployment

1. Bootstrap CDK (if not done before):
```bash
cdk bootstrap
```

2. Deploy the stack:
```bash
cdk deploy --parameters CloudtrailLocation=s3://your-cloudtrail-bucket/AWSLogs/123456789123/CloudTrail/ --parameters StartDateParameter=2024/01/01
```

## Parameters

- **CloudtrailLocation**: S3 location of your CloudTrail logs
- **StartDateParameter**: Start date for CloudTrail data in YYYY/MM/DD format

## Deployment Order

Deploy after the Data Collection CDK stack to ensure S3 buckets exist.

## Resources Created

### Glue Database
- `admin-console-2025`: Main database for all tables

### Glue Tables
- `group_membership`: User and group information
- `object_access`: Object access permissions
- `folder_assets`: Folder asset relationships
- `folder_lk`: Folder permissions lookup
- `folder_path`: Folder hierarchy paths
- `cloudtrail_logs_pp`: Partitioned CloudTrail logs
- `data_dict`: Data dictionary
- `datasets_info`: Dataset information
- `q_topic_info`: QuickSight Q topics
- `q_object_access`: Q object access permissions
- `datasets_properties`: Dataset properties and metrics
- `datasource_property`: Dataset to datasource mapping
- `cw_qs_ds_{account-id}`: CloudWatch dataset metrics
- `cw_qs_dash_visual_{account-id}`: CloudWatch dashboard/visual metrics
- `cw_qs_spice_{account-id}`: CloudWatch SPICE metrics



### Glue Crawlers
- `crawler-cw-qs-ds`: CloudWatch dataset metrics crawler
- `crawler-cw-qs-spice`: CloudWatch SPICE metrics crawler
- `crawler-cw-qs-dash-visual`: CloudWatch dashboard/visual metrics crawler
- Scheduled partition management crawlers

## Cleanup

To remove all resources:
```bash
cdk destroy
```