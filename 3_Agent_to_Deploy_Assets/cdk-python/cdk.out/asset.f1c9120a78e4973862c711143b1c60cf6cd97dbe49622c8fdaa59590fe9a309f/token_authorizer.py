import json
import base64
import requests
import os

# Cognito configuration
USER_POOL_ID = os.environ.get('USER_POOL_ID', 'us-east-1_p7YlBR2h9')
REGION = os.environ.get('REGION', 'us-east-1')
COGNITO_ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"

def lambda_handler(event, context):
    """
    Lambda authorizer that validates tokens from Cognito using simple validation.
    """
    try:
        # Extract token from Authorization header
        token = event['authorizationToken'].replace('Bearer ', '')
        
        # Simple token validation - decode without verification for now
        # In production, you should verify the signature
        parts = token.split('.')
        if len(parts) != 3:
            raise Exception('Invalid token format')
        
        # Decode payload (add padding if needed)
        payload_b64 = parts[1]
        # Add padding if needed
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)
        
        # Check issuer
        if payload.get('iss') != COGNITO_ISSUER:
            raise Exception('Invalid issuer')
        
        # Check token type and validate accordingly
        token_use = payload.get('token_use')
        
        if token_use == 'id':
            # ID token validation
            client_id = payload.get('aud')
            if not client_id:
                raise Exception('Invalid ID token: missing audience')
        elif token_use == 'access':
            # Access token validation
            client_id = payload.get('client_id')
            if not client_id:
                raise Exception('Invalid access token: missing client_id')
            
            # Check scopes for API access
            scope = payload.get('scope', '')
            if 'biops-api/read' not in scope and 'biops-api/write' not in scope:
                raise Exception('Insufficient scopes for API access')
        else:
            raise Exception(f'Invalid token_use: {token_use}')
        
        # Generate policy
        policy = generate_policy('user', 'Allow', event['methodArn'])
        
        # Add user context
        policy['context'] = {
            'sub': payload.get('sub', ''),
            'client_id': client_id,
            'token_use': token_use,
            'scope': payload.get('scope', '')
        }
        
        return policy
        
    except Exception as e:
        print(f"Authorization failed: {str(e)}")
        # Return deny policy
        return generate_policy('user', 'Deny', event['methodArn'])

def generate_policy(principal_id, effect, resource):
    """Generate IAM policy for API Gateway."""
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }