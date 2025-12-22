import boto3
import json

def get_user_token():
    """Get ID token for API testing using Cognito admin authentication."""
    
    session = boto3.Session(profile_name='tools-account')
    client = session.client('cognito-idp', region_name='us-east-1')
    
    try:
        # Admin initiate auth
        response = client.admin_initiate_auth(
            UserPoolId='us-east-1_p7YlBR2h9',
            ClientId='6gepfa9rjuqcn2ql0k3na71417',  # Original client without secret
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': 'test@example.com',
                'PASSWORD': 'NewPassword123!'
            }
        )
        
        # Extract tokens
        auth_result = response['AuthenticationResult']
        id_token = auth_result['IdToken']
        access_token = auth_result['AccessToken']
        
        print("✅ Authentication successful!")
        print(f"ID Token: {id_token[:50]}...")
        print(f"Access Token: {access_token[:50]}...")
        
        return {
            'id_token': id_token,
            'access_token': access_token
        }
        
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None

def test_api_with_user_token():
    """Test API with user ID token."""
    import requests
    
    tokens = get_user_token()
    if not tokens:
        return
    
    # Test with ID token (what Cognito authorizer expects)
    headers = {
        'Authorization': f"Bearer {tokens['id_token']}",
        'Content-Type': 'application/json'
    }
    
    payload = {
        "source_account_id": "499080683179",
        "source_role_name": "BiopsSourceAccountRole",
        "source_asset_id": "d41a3c00-e581-4ec2-969c-4778562bedd3",
        "aws_region": "us-east-1"
    }
    
    print("\n🚀 Testing export endpoint with ID token...")
    response = requests.post(
        'https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod/export',
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_api_with_user_token()