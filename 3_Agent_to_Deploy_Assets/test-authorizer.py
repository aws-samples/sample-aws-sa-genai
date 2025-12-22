#!/usr/bin/env python3
import json
import boto3

def test_authorizer():
    """Test the Lambda authorizer directly."""
    
    session = boto3.Session(profile_name='tools-account')
    lambda_client = session.client('lambda', region_name='us-east-1')
    
    # Get a token first
    import requests
    import base64
    
    CLIENT_ID = "2ii86s6r14g9p4rrts9ajtjrhu"
    CLIENT_SECRET = "1ls5730u8r2ohbdu0k7r08kog6ub041tivnbg0ud8q4j116tm2c0"
    COGNITO_DOMAIN = "biops-038198578763.auth.us-east-1.amazoncognito.com"
    
    # Get token
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "biops-api/read biops-api/write"
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    token_data = response.json()
    access_token = token_data.get('access_token')
    
    print(f"Got token: {access_token[:50]}...")
    
    # Test authorizer
    test_event = {
        "type": "TOKEN",
        "authorizationToken": f"Bearer {access_token}",
        "methodArn": "arn:aws:execute-api:us-east-1:038198578763:1cv3q605h2/prod/GET/jobs"
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='biops-token-authorizer',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        print("Authorizer Response:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error testing authorizer: {str(e)}")

if __name__ == "__main__":
    test_authorizer()