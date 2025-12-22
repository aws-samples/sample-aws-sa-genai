#!/bin/bash

# BIOPS API Testing with Authentication

# Cognito configuration
COGNITO_DOMAIN="biops-038198578763.auth.us-east-1.amazoncognito.com"
CLIENT_ID="59l0tiunr66f1ukmebeo3f330b"
CLIENT_SECRET="10r09b3f7c1j2l3l40lm3d3vqd3vq5j5q9f271nf3tni7grpevf8"
API_BASE_URL="https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod"

echo "🔐 Getting access token..."

# Get access token using client credentials
TOKEN_RESPONSE=$(curl -s -X POST "https://$COGNITO_DOMAIN/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic $(echo -n "$CLIENT_ID:$CLIENT_SECRET" | base64)" \
  -d "grant_type=client_credentials&scope=biops-api/read biops-api/write")

echo "Token response: $TOKEN_RESPONSE"

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token"
    echo "Error: $(echo "$TOKEN_RESPONSE" | jq -r '.error // .message // "Unknown error"')"
    exit 1
fi

echo "✅ Access token obtained"

# Test export endpoint
echo "🚀 Testing export endpoint..."

curl -X POST "$API_BASE_URL/export" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_account_id": "499080683179",
    "source_role_name": "BiopsSourceAccountRole", 
    "source_asset_id": "d41a3c00-e581-4ec2-969c-4778562bedd3",
    "aws_region": "us-east-1"
  }' | jq '.'

echo ""
echo "📋 Manual testing URLs:"
echo "Auth URL: https://$COGNITO_DOMAIN/oauth2/authorize?client_id=$CLIENT_ID&response_type=code&scope=openid+email+profile+biops-api/read+biops-api/write&redirect_uri=https://us-east-1.quicksight.aws.amazon.com/sn/oauthcallback"
echo ""
echo "Test credentials:"
echo "Email: test@example.com"
echo "Password: NewPassword123!"