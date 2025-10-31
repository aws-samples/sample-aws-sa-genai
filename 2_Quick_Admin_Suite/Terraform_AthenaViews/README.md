# QuickSight Admin Suite Athena Views - Terraform

This Terraform configuration creates Athena named queries (views) for the QuickSight Admin Suite analytical reporting.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured
- Appropriate AWS permissions
- Data Collection and Data Model stacks deployed first

## Usage

1. Initialize Terraform:
```bash
terraform init
```

2. Plan the deployment:
```bash
terraform plan -var="cur_source_table=billing.cur"
```

3. Apply the configuration:
```bash
terraform apply -var="cur_source_table=billing.cur"
```

## Variables

- `cur_source_table`: CUR database and table name (format: database.table_name)

## Deployment Order

Deploy after both Data Collection and Data Model Terraform configurations to ensure all required tables exist.

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
terraform destroy
```