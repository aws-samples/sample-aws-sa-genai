# QuickSight Admin Suite Data Model - CDK Version

This CDK application creates the data model infrastructure for the QuickSight Admin Suite, including Glue tables, Athena views, and crawlers for data analysis.

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
cdk deploy --parameters CloudtrailLocation=s3://your-cloudtrail-bucket/AWSLogs/123456789123/CloudTrail/ --parameters StartDateParameter=2024/01/01 --parameters CURSourceTable=billing.cur
```

## Parameters

- **CloudtrailLocation**: S3 location of your CloudTrail logs
- **StartDateParameter**: Start date for CloudTrail data in YYYY/MM/DD format
- **CURSourceTable**: CUR database and table name (format: database.table_name)

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
cdk destroy
```