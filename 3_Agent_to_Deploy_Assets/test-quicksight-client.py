import boto3
import hmac
import hashlib
import base64
import requests

def calculate_secret_hash(username, client_id, client_secret):
    """Calculate SECRET_HASH for Cognito authentication."""
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('UTF-8'),
        message.encode('UTF-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def get_token_with_quicksight_client():
    """Get ID token using QuickSight client with SECRET_HASH."""
    
    session = boto3.Session(profile_name='tools-account')
    client = session.client('cognito-idp', region_name='us-east-1')
    
    client_id = '42lmb828609l3i31fule2h70m5'
    client_secret = '172gqgvv8ud16ksnv8fk3ja9jgffl81d8sugjtjim2ejdh91vqu6'
    username = 'test@example.com'
    password = 'NewPassword123!'
    
    # Calculate SECRET_HASH
    secret_hash = calculate_secret_hash(username, client_id, client_secret)
    
    try:
        response = client.admin_initiate_auth(
            UserPoolId='us-east-1_p7YlBR2h9',
            ClientId=client_id,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
        )
        
        auth_result = response['AuthenticationResult']
        id_token = auth_result['IdToken']
        access_token = auth_result['AccessToken']
        
        print("✅ QuickSight client authentication successful!")
        print(f"ID Token: {id_token[:50]}...")
        print(f"Access Token: {access_token[:50]}...")
        
        return {
            'id_token': id_token,
            'access_token': access_token
        }
        
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None

def test_api_with_quicksight_token():
    """Test API with QuickSight client token."""
    
    tokens = get_token_with_quicksight_client()
    if not tokens:
        return
    
    # Test with ID token
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
    
    print("\n🚀 Testing export endpoint with QuickSight client ID token...")
    response = requests.post(
        'https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod/export',
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_api_with_quicksight_token()