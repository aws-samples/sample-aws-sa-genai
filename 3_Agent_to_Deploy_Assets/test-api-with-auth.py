import requests
import json
import base64
from urllib.parse import urlencode, parse_qs

# Cognito configuration
COGNITO_DOMAIN = "biops-038198578763.auth.us-east-1.amazoncognito.com"
CLIENT_ID = "42lmb828609l3i31fule2h70m5"
CLIENT_SECRET = "172gqgvv8ud16ksnv8fk3ja9jgffl81d8sugjtjim2ejdh91vqu6"
REDIRECT_URI = "https://us-east-1.quicksight.aws.amazon.com/sn/oauthcallback"
API_BASE_URL = "https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod"

def get_access_token_client_credentials():
    """Get access token using client credentials flow."""
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    
    # Create Basic Auth header
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": "biops-api/read biops-api/write"
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"Token request failed: {response.status_code} - {response.text}")
        return None

def test_export_with_auth():
    """Test the export endpoint with authentication."""
    
    # Get access token
    print("Getting access token...")
    access_token = get_access_token_client_credentials()
    
    if not access_token:
        print("Failed to get access token")
        return
    
    print("Access token obtained successfully")
    
    # Test export endpoint
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "source_account_id": "499080683179",
        "source_role_name": "BiopsSourceAccountRole",
        "source_asset_id": "d41a3c00-e581-4ec2-969c-4778562bedd3",
        "aws_region": "us-east-1"
    }
    
    print("Testing export endpoint...")
    response = requests.post(f"{API_BASE_URL}/export", headers=headers, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response

def get_authorization_url():
    """Generate authorization URL for manual testing."""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile biops-api/read biops-api/write",
        "redirect_uri": REDIRECT_URI
    }
    
    auth_url = f"https://{COGNITO_DOMAIN}/oauth2/authorize?" + urlencode(params)
    return auth_url

def exchange_code_for_token(authorization_code):
    """Exchange authorization code for tokens."""
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": REDIRECT_URI
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Token exchange failed: {response.status_code} - {response.text}")
        return None

def manual_auth_flow():
    """Manual authentication flow for testing."""
    print("=== Manual Authentication Flow ===")
    print("1. Visit this URL in your browser:")
    print(get_authorization_url())
    print("\n2. Sign in with your credentials:")
    print("   Email: test@example.com")
    print("   Password: NewPassword123!")
    print("\n3. After redirect, copy the 'code' parameter from the URL")
    print("4. Use exchange_code_for_token(code) to get tokens")

if __name__ == "__main__":
    print("BIOPS API Authentication Test")
    print("=" * 40)
    
    # Option 1: Try client credentials flow
    print("Testing with client credentials flow...")
    test_export_with_auth()
    
    print("\n" + "=" * 40)
    print("If client credentials doesn't work, use manual flow:")
    manual_auth_flow()