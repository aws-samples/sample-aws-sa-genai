#!/bin/bash

# BIOPS UI Deployment Script

set -e

# Configuration
STACK_NAME="biops-ui-stack"
REGION="us-east-1"
API_URL=${1:-"https://your-api-id.execute-api.us-east-1.amazonaws.com/prod"}

echo "Deploying BIOPS UI..."
echo "API URL: $API_URL"

# Create .env file
echo "REACT_APP_API_URL=$API_URL" > .env

# Install dependencies
echo "Installing dependencies..."
npm install

# Build React app
echo "Building React app..."
npm run build

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file deploy.yaml \
  --stack-name $STACK_NAME \
  --region $REGION \
  --no-fail-on-empty-changeset

# Get bucket name from stack outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

# Upload build files to S3
echo "Uploading files to S3 bucket: $BUCKET_NAME"
aws s3 sync build/ s3://$BUCKET_NAME --delete

# Get CloudFront URL
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text)

echo "Deployment complete!"
echo "CloudFront URL: $CLOUDFRONT_URL"
echo "Note: CloudFront may take 10-15 minutes to propagate changes."