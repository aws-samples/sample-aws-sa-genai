# BIOPS Python CDK Infrastructure

AWS CDK stack in Python for deploying BIOPS asset deployment infrastructure.

## Resources Created

- **Lambda Functions**: 6 functions for asset deployment workflow
- **DynamoDB Table**: Job status tracking with streams
- **API Gateway**: REST API with CORS enabled
- **IAM Roles**: Least privilege permissions for Lambda functions
- **Lambda Layer**: Shared utilities across functions

## Prerequisites

- Python 3.8+ installed
- AWS CLI configured
- CDK CLI installed: `npm install -g aws-cdk`

## Deployment

### Quick Deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual Deploy
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap
cdk deploy
```

## Stack Components

### Lambda Functions
- `biops-export-assets` - Export QuickSight assets
- `biops-upload-assets` - Upload bundles to S3
- `biops-import-assets` - Import assets to target account
- `biops-update-permissions` - Update asset permissions
- `biops-orchestrator` - Workflow orchestration
- `biops-job-api` - API Gateway handler

### API Endpoints
- `POST /jobs` - Start new deployment job
- `GET /jobs` - List all jobs
- `GET /jobs/{jobId}` - Get job details
- `POST /export` - Start asset export
- `GET /export/{exportJobId}` - Check export status
- `POST /upload` - Upload assets to S3
- `POST /import` - Import assets
- `GET /import/{importJobId}` - Check import status
- `POST /permissions` - Update asset permissions

### DynamoDB Table
- Table: `biops-job-runs`
- Partition Key: `jobId`
- Streams enabled for real-time updates
- Pay-per-request billing

## Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Synthesize CloudFormation template
cdk synth

# Deploy
cdk deploy

# Destroy
cdk destroy
```

## File Structure

```
cdk-python/
├── app.py              # CDK app entry point
├── biops_stack.py      # Main stack definition
├── requirements.txt    # Python dependencies
├── cdk.json           # CDK configuration
├── deploy.sh          # Deployment script
└── README.md          # This file
```