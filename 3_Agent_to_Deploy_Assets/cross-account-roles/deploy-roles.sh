#!/bin/bash

# Deploy cross-account IAM roles for BIOPS

TOOLS_ACCOUNT_ID=${1}
SOURCE_ACCOUNT_ID=${2}
TARGET_ACCOUNT_ID=${3}
REGION=${4:-"us-east-1"}

if [ -z "$TOOLS_ACCOUNT_ID" ] || [ -z "$SOURCE_ACCOUNT_ID" ] || [ -z "$TARGET_ACCOUNT_ID" ]; then
    echo "Usage: $0 <TOOLS_ACCOUNT_ID> <SOURCE_ACCOUNT_ID> <TARGET_ACCOUNT_ID> [REGION]"
    echo "Example: $0 038198578763 123456789012 210987654321 us-east-1"
    exit 1
fi

echo "Deploying cross-account roles for BIOPS..."
echo "Tools Account: $TOOLS_ACCOUNT_ID"
echo "Source Account: $SOURCE_ACCOUNT_ID"
echo "Target Account: $TARGET_ACCOUNT_ID"

# Deploy source account role
echo "Deploying source account role..."
aws cloudformation deploy \
  --template-file source-account-role.yaml \
  --stack-name biops-source-role \
  --parameter-overrides \
    ToolsAccountId=$TOOLS_ACCOUNT_ID \
    LambdaRoleName=BiopsStack-BiopsLambdaRole58B3079D-qJqsVNLyYLQA \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION \
  --profile source-account

# Deploy target account role
echo "Deploying target account role..."
aws cloudformation deploy \
  --template-file target-account-role.yaml \
  --stack-name biops-target-role \
  --parameter-overrides \
    ToolsAccountId=$TOOLS_ACCOUNT_ID \
    LambdaRoleName=BiopsStack-BiopsLambdaRole58B3079D-qJqsVNLyYLQA \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION \
  --profile target-account

# Deploy bucket policy in tools account
echo "Deploying bucket policy in tools account..."
aws cloudformation deploy \
  --template-file tools-account-bucket-policy.yaml \
  --stack-name biops-bucket-policy \
  --parameter-overrides \
    ToolsAccountId=$TOOLS_ACCOUNT_ID \
    SourceAccountIds="$SOURCE_ACCOUNT_ID,$TARGET_ACCOUNT_ID" \
  --region $REGION \
  --profile tools-account

echo "Cross-account roles deployed successfully!"
echo ""
echo "Role ARNs:"
echo "Source: arn:aws:iam::$SOURCE_ACCOUNT_ID:role/BiopsSourceAccountRole"
echo "Target: arn:aws:iam::$TARGET_ACCOUNT_ID:role/BiopsTargetAccountRole"