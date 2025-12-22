import jwt
import json
import requests
import boto3
import hmac
import hashlib
import base64

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
        return {
            'id_token': auth_result['IdToken'],
            'access_token': auth_result['AccessToken']
        }
        
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None

def decode_jwt_token(token):
    """Decode JWT token without verification to inspect claims."""
    try:
        # Decode without verification to see the payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def test_token_formats():
    """Test different token formats with the API."""
    
    print("🔍 Getting tokens from QuickSight client...")
    tokens = get_token_with_quicksight_client()
    
    if not tokens:
        print("❌ Failed to get tokens")
        return
    
    # Decode and inspect both tokens
    print("\n📋 ID Token Claims:")
    id_claims = decode_jwt_token(tokens['id_token'])
    if id_claims:
        print(json.dumps(id_claims, indent=2))
    
    print("\n📋 Access Token Claims:")
    access_claims = decode_jwt_token(tokens['access_token'])
    if access_claims:
        print(json.dumps(access_claims, indent=2))
    
    # Test API with both token types
    payload = {
        "source_account_id": "499080683179",
        "source_role_name": "BiopsSourceAccountRole",
        "source_asset_id": "d41a3c00-e581-4ec2-969c-4778562bedd3",
        "aws_region": "us-east-1"
    }
    
    print("\n🧪 Testing API with ID Token...")
    headers_id = {
        'Authorization': f"Bearer {tokens['id_token']}",
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod/export',
        headers=headers_id,
        json=payload
    )
    print(f"ID Token - Status: {response.status_code}, Response: {response.text}")
    
    print("\n🧪 Testing API with Access Token...")
    headers_access = {
        'Authorization': f"Bearer {tokens['access_token']}",
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod/export',
        headers=headers_access,
        json=payload
    )
    print(f"Access Token - Status: {response.status_code}, Response: {response.text}")

def test_manual_token():
    """Test with a manually provided token."""
    print("\n🔧 Manual Token Test")
    print("If you have a token from QuickSight, paste it here:")
    
    # For testing - you can paste a token here
    manual_token = input("Token (or press Enter to skip): ").strip()
    
    if manual_token:
        print("\n📋 Manual Token Claims:")
        claims = decode_jwt_token(manual_token)
        if claims:
            print(json.dumps(claims, indent=2))
        
        headers = {
            'Authorization': f"Bearer {manual_token}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            "source_account_id": "499080683179",
            "source_role_name": "BiopsSourceAccountRole",
            "source_asset_id": "d41a3c00-e581-4ec2-969c-4778562bedd3",
            "aws_region": "us-east-1"
        }
        
        response = requests.post(
            'https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod/export',
            headers=headers,
            json=payload
        )
        print(f"Manual Token - Status: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    test_token_formats()
    test_manual_token()