#!/bin/bash

# Configure OAuth Authentication Script
# Run this after CDK deployment to update UI configuration

echo "🔧 Configuring OAuth Authentication..."

# Get CDK stack outputs
STACK_NAME="BiopsStack"
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)
CLIENT_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' --output text)
COGNITO_DOMAIN=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`CognitoDomain`].OutputValue' --output text)
API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📋 Configuration Values:"
echo "User Pool ID: $USER_POOL_ID"
echo "Client ID: $CLIENT_ID"
echo "Cognito Domain: $COGNITO_DOMAIN"
echo "API URL: $API_URL"
echo "Account ID: $ACCOUNT_ID"

# Update auth.js
echo "📝 Updating ui/src/auth.js..."
sed -i.bak "s/YOUR_USER_POOL_CLIENT_ID/$CLIENT_ID/g" ui/src/auth.js
sed -i.bak "s/YOUR_ACCOUNT_ID/$ACCOUNT_ID/g" ui/src/auth.js
sed -i.bak "s/YOUR_USER_POOL_ID/$USER_POOL_ID/g" ui/src/auth.js

# Update api.js
echo "📝 Updating ui/src/api.js..."
sed -i.bak "s|https://your-api-id.execute-api.us-east-1.amazonaws.com/prod|$API_URL|g" ui/src/api.js

echo "✅ Configuration complete!"
echo ""
echo "🚀 Next steps:"
echo "1. cd ui && npm install"
echo "2. npm start"
echo "3. Create test user:"
echo "   aws cognito-idp admin-create-user --user-pool-id $USER_POOL_ID --username testuser --user-attributes Name=email,Value=test@example.com --temporary-password TempPass123! --message-action SUPPRESS"
echo "4. Set permanent password:"
echo "   aws cognito-idp admin-set-user-password --user-pool-id $USER_POOL_ID --username testuser --password NewPassword123! --permanent"