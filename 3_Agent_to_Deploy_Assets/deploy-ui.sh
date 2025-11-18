#!/bin/bash

# Deploy UI to AWS Amplify
echo "🚀 Deploying UI to AWS Amplify..."

# Get Amplify App ID from CDK outputs
AMPLIFY_APP_ID=$(aws cloudformation describe-stacks --stack-name BiopsStack --query 'Stacks[0].Outputs[?OutputKey==`AmplifyAppId`].OutputValue' --output text --profile tools-account --region us-east-1)

echo "📋 Amplify App ID: $AMPLIFY_APP_ID"

# Build the React app
echo "🔨 Building React app..."
cd ui
npm run build

# Create deployment zip
echo "📦 Creating deployment package..."
cd build
zip -r ../deployment.zip .
cd ..

# Deploy to Amplify
echo "🚀 Deploying to Amplify..."
aws amplify create-deployment \
  --app-id $AMPLIFY_APP_ID \
  --branch-name main \
  --profile tools-account \
  --region us-east-1

# Get the deployment job ID and upload URL
DEPLOYMENT_INFO=$(aws amplify create-deployment --app-id $AMPLIFY_APP_ID --branch-name main --profile tools-account --region us-east-1)
JOB_ID=$(echo $DEPLOYMENT_INFO | jq -r '.jobId')
UPLOAD_URL=$(echo $DEPLOYMENT_INFO | jq -r '.zipUploadUrl')

echo "📤 Uploading build files..."
curl -X PUT "$UPLOAD_URL" --data-binary @deployment.zip

# Start the deployment
echo "▶️ Starting deployment..."
aws amplify start-deployment \
  --app-id $AMPLIFY_APP_ID \
  --branch-name main \
  --job-id $JOB_ID \
  --profile tools-account \
  --region us-east-1

echo "✅ Deployment initiated!"
echo "🌐 App URL: https://main.$AMPLIFY_APP_ID.amplifyapp.com"
echo "📊 Monitor deployment: https://console.aws.amazon.com/amplify/home?region=us-east-1#/$AMPLIFY_APP_ID"