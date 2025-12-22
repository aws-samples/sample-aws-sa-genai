# QuickSight OAuth Integration Solution

## Problem
QuickSight is failing at step 3 (token exchange) with "No access token was found for an OAuth authorization code connection" error.

## Root Cause
QuickSight requires machine-to-machine authentication but the current setup has conflicting OAuth flows and API Gateway authorizer configuration issues.

## Solution

### 1. Machine-to-Machine Client Created ✅
- **Client ID**: `2ii86s6r14g9p4rrts9ajtjrhu`
- **Client Secret**: `1ls5730u8r2ohbdu0k7r08kog6ub041tivnbg0ud8q4j116tm2c0`
- **OAuth Flow**: `client_credentials` only
- **Scopes**: `biops-api/read`, `biops-api/write`

### 2. Token Exchange Working ✅
The client credentials flow is working correctly:
```bash
curl -X POST https://biops-038198578763.auth.us-east-1.amazoncognito.com/oauth2/token \
  -H "Authorization: Basic MmlpODZzNnIxNGc5cDRycnRzOWFqdGpyaHU6MWxzNTczMHU4cjJvaGJkdTBrN3IwOGtvZzZ1YjA0MXRpdm5iZzB1ZDhxNGoxMTZ0bTJjMA==" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&scope=biops-api/read biops-api/write"
```

### 3. API Gateway Authorizer Issue ❌
The API Gateway Cognito authorizer is rejecting access tokens from the M2M client. This needs to be fixed.

## QuickSight Configuration

### For QuickSight Action Connector:
1. **OAuth Client ID**: `2ii86s6r14g9p4rrts9ajtjrhu`
2. **OAuth Client Secret**: `1ls5730u8r2ohbdu0k7r08kog6ub041tivnbg0ud8q4j116tm2c0`
3. **Authorization URL**: `https://biops-038198578763.auth.us-east-1.amazoncognito.com/oauth2/authorize`
4. **Token URL**: `https://biops-038198578763.auth.us-east-1.amazoncognito.com/oauth2/token`
5. **Scopes**: `biops-api/read biops-api/write`
6. **Grant Type**: `client_credentials`

### Alternative: Use Authorization Code Flow Client
If QuickSight requires authorization code flow, use the existing client:
- **Client ID**: `13m1ionmfagtidvo094r90lq4a` 
- **Client Secret**: `1vjeuqjftl6svdj5vnm31kh8o9lei539n3sb9eq8mi266reik5sl`
- **Callback URL**: `https://us-east-1.quicksight.aws.amazon.com/sn/oauthcallback`

## Next Steps

### Option 1: Fix API Gateway Authorizer (Recommended)
Update the API Gateway Cognito authorizer to accept access tokens from both user authentication and machine-to-machine clients.

### Option 2: Create Lambda Authorizer
Replace Cognito authorizer with a custom Lambda authorizer that can validate both ID tokens and access tokens.

### Option 3: Use Different Authentication
Configure QuickSight to use API keys or IAM authentication instead of OAuth.

## Testing Commands

### Test M2M Authentication:
```bash
python test-m2m-auth.py
```

### Test with cURL:
```bash
# Get token
TOKEN=$(curl -s -X POST https://biops-038198578763.auth.us-east-1.amazoncognito.com/oauth2/token \
  -H "Authorization: Basic MmlpODZzNnIxNGc5cDRycnRzOWFqdGpyaHU6MWxzNTczMHU4cjJvaGJkdTBrN3IwOGtvZzZ1YjA0MXRpdm5iZzB1ZDhxNGoxMTZ0bTJjMA==" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&scope=biops-api/read biops-api/write" | jq -r .access_token)

# Test API
curl -H "Authorization: Bearer $TOKEN" https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod/jobs
```

## Status
- ✅ M2M client created and working
- ✅ Token exchange successful  
- ❌ API Gateway authorization failing
- ❌ QuickSight integration pending API fix