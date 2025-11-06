# QuickSight Admin Suite - Glue Scripts

This directory contains AWS Glue job scripts for comprehensive QuickSight monitoring and analytics.

## Directory Structure

```
Glue/
├── NewTemplates/           # Optimized scripts (recommended)
│   ├── admin_suite_dataset.py
│   ├── admin_suite_datasource.py
│   ├── admin_suite_folder.py
│   ├── admin_suite_q.py
│   ├── admin_suite_user_info_access_manage.py
│   └── README.md
└── README.md              # This file
```

## Recommended Usage

Use the scripts in the `NewTemplates/` directory for:
- **Better Performance**: 50% fewer API calls through optimized combinations
- **Cleaner Architecture**: Standardized parameters and error handling
- **Easier Maintenance**: Consolidated functionality with consistent naming

## Migration from Legacy Scripts

If migrating from older QuickSight admin solutions, the `NewTemplates/` scripts provide equivalent functionality with improved efficiency:

- **Dataset Operations**: Combined dataset properties and data dictionary collection
- **Q Topic Operations**: Combined Q topic metadata and access permissions
- **Standardized Parameters**: All scripts use `AWS_REGION` and `S3_OUTPUT_PATH`
- **Enhanced Error Handling**: Robust exception handling for missing resources

## Getting Started

1. Deploy using the CloudFormation template: `CFT/NewTemplates/quick_admin_suite_data_collection.template`
2. Scripts will run automatically every 3 hours
3. Monitor outputs in your configured S3 bucket under `monitoring/quicksight/`

For detailed script documentation, see `NewTemplates/README.md`.