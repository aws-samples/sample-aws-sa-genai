#!/bin/bash

# Deploy BIOPS Asset Bundle Lambda Functions

# Configuration
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role"

# Create deployment packages
echo "Creating deployment packages..."

# Create shared layer
mkdir -p layer/python
cp -r shared layer/python/
cd layer
zip -r ../shared-layer.zip .
cd ..

# Deploy shared layer
aws lambda publish-layer-version \
    --layer-name biops-shared-layer \
    --zip-file fileb://shared-layer.zip \
    --compatible-runtimes python3.9 \
    --region $REGION

LAYER_ARN=$(aws lambda list-layer-versions --layer-name biops-shared-layer --region $REGION --query 'LayerVersions[0].LayerVersionArn' --output text)

# Deploy export function
cd export_assets
zip -r ../export-assets.zip .
cd ..

aws lambda create-function \
    --function-name biops-export-assets \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://export-assets.zip \
    --timeout 300 \
    --layers $LAYER_ARN \
    --region $REGION

# Deploy upload function
cd upload_assets
zip -r ../upload-assets.zip .
cd ..

aws lambda create-function \
    --function-name biops-upload-assets \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://upload-assets.zip \
    --timeout 300 \
    --layers $LAYER_ARN \
    --region $REGION

# Deploy import function
cd import_assets
zip -r ../import-assets.zip .
cd ..

aws lambda create-function \
    --function-name biops-import-assets \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://import-assets.zip \
    --timeout 300 \
    --layers $LAYER_ARN \
    --region $REGION

# Deploy permissions function
cd update_permissions
zip -r ../update-permissions.zip .
cd ..

aws lambda create-function \
    --function-name biops-update-permissions \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://update-permissions.zip \
    --timeout 300 \
    --layers $LAYER_ARN \
    --region $REGION

# Deploy orchestrator function
cd orchestrator
zip -r ../orchestrator.zip .
cd ..

aws lambda create-function \
    --function-name biops-orchestrator \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://orchestrator.zip \
    --timeout 900 \
    --region $REGION

echo "Deployment complete!"