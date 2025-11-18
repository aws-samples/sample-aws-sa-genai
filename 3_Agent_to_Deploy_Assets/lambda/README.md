# BIOPS Asset Deployment Lambda Functions

This directory contains Lambda functions that implement the QuickSight asset deployment workflow as bundle APIs, based on the notebook implementation.

## Architecture

The solution consists of 5 Lambda functions:

1. **biops-export-assets** - Exports QuickSight assets from source account
2. **biops-upload-assets** - Downloads and uploads asset bundle to tools account S3
3. **biops-import-assets** - Imports assets into target account from tools account S3
4. **biops-update-permissions** - Updates permissions for imported assets
5. **biops-orchestrator** - Orchestrates the complete workflow

## Deployment

1. Update the `ROLE_ARN` in `deploy.sh` with your Lambda execution role
2. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## Usage

### Complete Workflow (Recommended)
Use the orchestrator function for end-to-end deployment:

```python
import boto3
import json

lambda_client = boto3.client('lambda')

config = {
    "source_account_id": "123456789012",
    "source_role_name": "QuickSightRole", 
    "source_asset_id": "dashboard-id-123",
    "target_account_id": "210987654321",
    "target_role_name": "QuickSightRole",
    "target_admin_user": "admin-user",
    "bucket_name": "biops-version-control-demo-038198578763",
    "dashboard_name": "BIOpsDemo"
}

response = lambda_client.invoke(
    FunctionName='biops-orchestrator',
    Payload=json.dumps({'config': config})
)
```

### Individual Functions
Each function can be called independently for custom workflows. See `lambda_invoke_example.py` for details.

## API Endpoints

| Method | Endpoint | Function | Purpose |
|--------|----------|----------|---------|
| `POST` | `/jobs` | biops-orchestrator | Full workflow orchestration |
| `GET` | `/jobs` | biops-job-api | List all jobs |
| `GET` | `/jobs/{jobId}` | biops-job-api | Get job details |
| `POST` | `/export` | biops-export-assets | Start QuickSight export |
| `GET` | `/export/{exportJobId}` | biops-export-assets | Check export status |
| `POST` | `/upload` | biops-upload-assets | Upload bundle to S3 |
| `POST` | `/import` | biops-import-assets | Start QuickSight import |
| `GET` | `/import/{importJobId}` | biops-import-assets | Check import status |
| `POST` | `/permissions` | biops-update-permissions | Update asset permissions |

## Required IAM Permissions

The Lambda execution role needs:
- QuickSight permissions for asset export/import
- S3 permissions for bucket access
- STS permissions for cross-account role assumption
- Lambda invoke permissions for orchestrator

## Configuration

Functions expect configuration parameters matching the original notebook:
- Account IDs and role names for source/target accounts
- Asset IDs and bucket names
- Admin user for permissions setup