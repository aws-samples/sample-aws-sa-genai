# QuickSight Admin Suite Athena Views - CDK Version

This CDK application creates Athena named queries (views) for the QuickSight Admin Suite analytical reporting.

## Prerequisites

- AWS CDK CLI installed
- Python 3.7 or later
- AWS credentials configured
- Data Collection and Data Model stacks deployed first

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
cdk deploy --parameters CURSourceTable=billing.cur
```

## Parameters

- **CURSourceTable**: CUR database and table name (format: database.table_name)

## Deployment Order

Deploy after both Data Collection and Data Model CDK stacks to ensure all required tables exist.

## Resources Created

### Athena Named Queries
- `quicksight_crud_events_view`: QuickSight CRUD operations from CloudTrail
- `quicksight_querydb_events_view`: QuickSight database query events
- `qs_usage_cur_vw`: QuickSight usage and cost analysis from CUR data
- `cw_qs_ds_pivot_view`: Pivoted CloudWatch dataset metrics
- `cw_qs_dash_visual_pivot_view`: Pivoted CloudWatch dashboard/visual metrics
- `cw_qs_spice_pivot_view`: Pivoted CloudWatch SPICE capacity metrics
- `cw_qs_qindex_pivot_view`: Pivoted CloudWatch Q Index metrics
- `qs_ds_info_combined_view`: Combined dataset properties and info

## Cleanup

To remove all resources:
```bash
cdk destroy
```