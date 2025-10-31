# Quick Admin Suite Data Collection - CDK

This CDK application converts the CloudFormation template for QuickSight Admin Suite data collection into AWS CDK Python code.

## Prerequisites

- Python 3.7+
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- AWS credentials configured

## Setup

1. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Deploy

1. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

2. Deploy the stack:
```bash
cdk deploy
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
- `etl_job_admin_suite_assets_access`: User and access data
- `etl_job_admin_suite_assets_metadata`: Dataset and dashboard metadata
- `etl_job_admin_suite_folder_assets`: Folder information
- `etl_job_admin_suite_q_access`: Q object access
- `etl_job_admin_suite_q_metadata`: Q topics metadata
- `etl_job_admin_suite_ds_properties`: Dataset properties
- `etl_job_admin_suite_datasource_properties`: Datasource properties

### Scheduled Triggers
- All Glue jobs scheduled to run every 3 hours

### CloudWatch Infrastructure
- 5 CloudWatch metric streams for different QuickSight metrics
- Kinesis Firehose delivery streams for metric data to S3

## Cleanup

```bash
cdk destroy
```

## Differences from CloudFormation

- Uses CDK constructs for better type safety and IDE support
- Automatic dependency management
- Simplified resource references
- Built-in best practices for security and configuration