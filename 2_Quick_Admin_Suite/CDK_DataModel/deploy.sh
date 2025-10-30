#!/bin/bash

# QuickSight Admin Suite Data Model Deployment Script

echo "Setting up QuickSight Admin Suite Data Model CDK deployment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if parameters are provided
if [ $# -lt 3 ]; then
    echo "Usage: $0 <CloudtrailLocation> <StartDateParameter> <CURSourceTable>"
    echo "Example: $0 's3://cloudtrail-bucket/AWSLogs/123456789123/CloudTrail/' '2024/01/01' 'billing.cur'"
    exit 1
fi

CLOUDTRAIL_LOCATION=$1
START_DATE=$2
CUR_SOURCE_TABLE=$3

echo "Deploying with parameters:"
echo "  CloudtrailLocation: $CLOUDTRAIL_LOCATION"
echo "  StartDateParameter: $START_DATE"
echo "  CURSourceTable: $CUR_SOURCE_TABLE"

# Bootstrap CDK if needed
echo "Checking CDK bootstrap status..."
cdk bootstrap

# Deploy the stack
echo "Deploying QuickSight Admin Suite Data Model stack..."
cdk deploy \
    --parameters CloudtrailLocation="$CLOUDTRAIL_LOCATION" \
    --parameters StartDateParameter="$START_DATE" \
    --parameters CURSourceTable="$CUR_SOURCE_TABLE" \
    --require-approval never

echo "Deployment completed!"