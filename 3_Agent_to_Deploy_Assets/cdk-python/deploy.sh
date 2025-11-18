#!/bin/bash

# BIOPS Python CDK Deployment Script

set -e

echo "Deploying BIOPS infrastructure with Python CDK..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Bootstrap CDK (if not already done)
echo "Bootstrapping CDK..."
cdk bootstrap

# Deploy stack
echo "Deploying BIOPS stack..."
cdk deploy --require-approval never

# Get API URL from stack outputs
API_URL=$(aws cloudformation describe-stacks \
  --stack-name BiopsStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

echo "Deployment complete!"
echo "API Gateway URL: $API_URL"
echo ""
echo "Next steps:"
echo "1. Update React UI .env file with API URL"
echo "2. Deploy React UI: cd ../ui && ./deploy.sh $API_URL"