import json
import jwt
import requests
from jwt.algorithms import RSAAlgorithm

# Cognito configuration
USER_POOL_ID = "us-east-1_p7YlBR2h9"
REGION = "us-east-1"
COGNITO_ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"

def lambda_handler(event, context):
    """
    Lambda authorizer that validates both ID tokens and access tokens from Cognito.
    """
    try:
        # Extract token from Authorization header
        token = event['authorizationToken'].replace('Bearer ', '')
        
        # Get Cognito public keys
        jwks_url = f"{COGNITO_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        
        # Decode token header to get key ID
        header = jwt.get_unverified_header(token)
        kid = header['kid']
        
        # Find the correct key
        key = None
        for jwk in jwks['keys']:
            if jwk['kid'] == kid:
                key = RSAAlgorithm.from_jwk(json.dumps(jwk))
                break
        
        if not key:
            raise Exception('Public key not found')
        
        # Verify and decode token
        payload = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            issuer=COGNITO_ISSUER,
            options={"verify_aud": False}  # Skip audience verification for access tokens
        )
        
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