# Cross-Account IAM Roles for BIOPS

This directory contains CloudFormation templates to set up cross-account access for the BIOPS asset deployment workflow.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Source Account │    │  Tools Account  │    │ Target Account  │
│                 │    │                 │    │                │
│ BiopsSourceRole │◄───┤ BiopsLambdaRole ├───►│ BiopsTargetRole │
│                 │    │                 │    │                │
│ QuickSight      │    │ Lambda + API    │    │ QuickSight      │
│ Dashboards      │    │ S3 Bucket       │    │ Import          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Files

- `source-account-role.yaml` - IAM role for QuickSight export access
- `target-account-role.yaml` - IAM role for QuickSight import access  
- `tools-account-bucket-policy.yaml` - S3 bucket policy for cross-account access
- `deploy-roles.sh` - Automated deployment script

## Deployment

### Prerequisites
Configure AWS CLI profiles:
- `source-account` - Source account credentials
- `target-account` - Target account credentials  
- `tools-account` - Tools account credentials

### Deploy All Roles
```bash
chmod +x deploy-roles.sh
./deploy-roles.sh TOOLS_ACCOUNT_ID SOURCE_ACCOUNT_ID TARGET_ACCOUNT_ID
```

**Example:**
```bash
./deploy-roles.sh 038198578763 123456789012 210987654321
```

### Manual Deployment

**1. Source Account:**
```bash
aws cloudformation deploy \
  --template-file source-account-role.yaml \
  --stack-name biops-source-role \
  --parameter-overrides ToolsAccountId=038198578763 \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile source-account
```

**2. Target Account:**
```bash
aws cloudformation deploy \
  --template-file target-account-role.yaml \
  --stack-name biops-target-role \
  --parameter-overrides ToolsAccountId=038198578763 \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile target-account
```

**3. Tools Account Bucket Policy:**
```bash
aws cloudformation deploy \
  --template-file tools-account-bucket-policy.yaml \
  --stack-name biops-bucket-policy \
  --parameter-overrides \
    ToolsAccountId=038198578763 \
    SourceAccountIds="123456789012,210987654321" \
  --profile tools-account
```

## Role Permissions

### Source Account Role
- `quicksight:StartAssetBundleExportJob`
- `quicksight:DescribeAssetBundleExportJob`
- `quicksight:List*` and `quicksight:Describe*` for assets

### Target Account Role  
- `quicksight:StartAssetBundleImportJob`
- `quicksight:DescribeAssetBundleImportJob`
- `quicksight:Update*Permissions`
- `s3:GetObject` from tools account bucket

### Tools Account Bucket
- Cross-account `s3:GetObject` and `s3:PutObject`
- Cross-account `s3:ListBucket`

## Usage in API Calls

Update your API calls to use the cross-account role ARNs:

```python
# Export from source account
export_payload = {
    "source_account_id": "123456789012",
    "source_role_name": "BiopsSourceAccountRole",
    "source_asset_id": "dashboard-id-123"
}

# Import to target account  
import_payload = {
    "target_account_id": "210987654321", 
    "target_role_name": "BiopsTargetAccountRole",
    "s3_uri": "s3://biops-version-control-demo-038198578763/bundle.zip"
}
```