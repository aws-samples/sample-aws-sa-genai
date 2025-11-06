# QuickSight Admin Suite - Glue Scripts

Optimized Glue job scripts for comprehensive QuickSight monitoring and analytics.

## Scripts Overview

| Script | Purpose | Outputs |
|--------|---------|----------|
| `admin_suite_dataset.py` | Dataset properties, lineage & data dictionary | `datasets_properties.csv`, `datsets_info.csv`, `data_dictionary.csv` |
| `admin_suite_datasource.py` | Dataset-to-datasource dependency mapping | `datasource_property.csv` |
| `admin_suite_folder.py` | Folder structure, permissions & assets | `folder_assets.csv`, `folder_lk.csv`, `folder_path.csv` |
| `admin_suite_q.py` | Q topic metadata & access permissions | `q_topics_info.csv`, `q_object_access.csv` |
| `admin_suite_user_info_access_manage.py` | User groups & asset permissions | `group_membership.csv`, `object_access.csv` |

## Key Features

- **Optimized Performance**: Combined related operations to reduce API calls by 50%
- **Consistent Parameters**: All scripts use standardized `AWS_REGION` and `S3_OUTPUT_PATH` parameters
- **Error Handling**: Robust exception handling for missing resources and API failures
- **S3 Integration**: Configurable output paths with automatic bucket validation

## Parameters

All scripts accept these standard parameters:
- `AWS_REGION`: AWS region for QuickSight operations
- `S3_OUTPUT_PATH`: Base S3 path for output files (e.g., `s3://admin-suite-123456789/monitoring/quicksight`)

Additional parameters:
- `AWS_ACCOUNT_ID`: Required for Q topic scripts
- `QUICKSIGHT_IDENTITY_REGION`: Required for datasource script

## CloudFormation Integration

These scripts are deployed via the `quick_admin_suite_data_collection.template` CloudFormation template with:
- Scheduled execution every 3 hours
- IAM role with appropriate QuickSight and S3 permissions
- Automatic S3 bucket creation and validation

## Output Structure

```
s3://admin-suite-{account-id}/monitoring/quicksight/
├── datasets_properties/
├── datsets_info/
├── data_dictionary/
├── datasource_property/
├── folder_assets/
├── folder_lk/
├── folder_path/
├── q_topics_info/
├── q_object_access/
├── group_membership/
└── object_access/
```