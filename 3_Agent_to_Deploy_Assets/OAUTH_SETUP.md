# OAuth Setup with Amazon Cognito

## Overview
This guide explains how to deploy and configure OAuth authentication using Amazon Cognito for the BIOPS API Gateway.

## Deployment Steps

### 1. Deploy the CDK Stack
```bash
cd cdk-python
cdk deploy
```

After deployment, note the following outputs:
- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Cognito User Pool Client ID  
- `CognitoDomain`: Cognito hosted UI domain
- `ApiUrl`: API Gateway endpoint URL

### 2. Update UI Configuration
Update `/ui/src/auth.js` with the deployment outputs:

```javascript
const authConfig = {
  ClientId: 'YOUR_USER_POOL_CLIENT_ID', // From CDK output
  AppWebDomain: 'biops-YOUR_ACCOUNT_ID.auth.us-east-1.amazoncognito.com', // From CDK output
  UserPoolId: 'YOUR_USER_POOL_ID', // From CDK output
  // ... rest of config
};
```

### 3. Update API Base URL
Update `/ui/src/api.js` with your API Gateway URL:

```javascript
const API_BASE_URL = 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';
```

### 4. Install Dependencies and Start UI
```bash
cd ui
npm install
npm start
```

## Authentication Flow

### 1. User Access
- User visits the application
- If not authenticated, redirected to login page
- Click "Sign In with Cognito" button

### 2. Cognito Hosted UI
- User redirected to Cognito hosted UI
- User can sign up or sign in
- After successful authentication, redirected back to app

### 3. API Calls
- All API calls automatically include JWT token in Authorization header
- API Gateway validates token using Cognito authorizer
- Invalid/expired tokens result in 401 response and automatic logout

## User Management

### Create Test User (via AWS CLI)
```bash
aws cognito-idp admin-create-user \
  --user-pool-id YOUR_USER_POOL_ID \
  --username testuser \
  --user-attributes Name=email,Value=test@example.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS
```

### Set Permanent Password
```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id YOUR_USER_POOL_ID \
  --username testuser \
  --password NewPassword123! \
  --permanent
```

## Security Features

### Password Policy
- Minimum 8 characters
- Requires uppercase, lowercase, numbers, and symbols
- Account recovery via email only

### Token Configuration
- JWT tokens include user email and username
- Tokens automatically refresh
- Secure token storage in browser

### API Protection
- All API endpoints require valid JWT token
- Cognito authorizer validates tokens
- Cross-origin requests properly configured

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure callback URLs are properly configured
   - Check API Gateway CORS settings

2. **Token Validation Errors**
   - Verify User Pool ID and Client ID are correct
   - Check token expiration

3. **Redirect Issues**
   - Ensure callback URLs match exactly
   - Check for trailing slashes

### Debug Steps
1. Check browser console for authentication errors
2. Verify CDK deployment outputs
3. Test API endpoints with valid tokens
4. Check Cognito User Pool configuration

## Production Considerations

### Custom Domain
- Configure custom domain for Cognito hosted UI
- Update callback URLs accordingly

### User Pool Configuration
- Configure additional user attributes as needed
- Set up email/SMS verification
- Configure password policies per requirements

### Monitoring
- Enable CloudWatch logs for API Gateway
- Monitor Cognito authentication metrics
- Set up alerts for failed authentication attempts