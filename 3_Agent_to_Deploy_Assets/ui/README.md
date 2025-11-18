# BIOPS UI with OAuth Authentication

## Quick Start

### Option 1: HTTPS (Recommended for OAuth)
```bash
npm run start:https
```
- App runs at: `https://localhost:3000`
- Accept the self-signed certificate warning in your browser
- OAuth authentication will work properly

### Option 2: HTTP (Limited functionality)
```bash
npm start
```
- App runs at: `http://localhost:3000`
- OAuth may not work due to browser security restrictions

## Test Credentials
- **Email**: `test@example.com`
- **Password**: `NewPassword123!`

## Authentication Flow
1. Visit `https://localhost:3000`
2. Click "Sign In with Cognito"
3. Enter test credentials
4. Get redirected back to the app
5. All API calls will include JWT tokens

## Troubleshooting

### Certificate Warning
- Browser will show "Not Secure" warning for self-signed certificate
- Click "Advanced" → "Proceed to localhost (unsafe)"
- This is normal for local development

### OAuth Redirect Issues
- Ensure you're using HTTPS version
- Check browser console for errors
- Verify Cognito configuration is correct

### API Authentication Errors
- Check that JWT tokens are being sent
- Verify API Gateway authorizer is working
- Check browser network tab for 401 errors