#!/usr/bin/env python3
import requests
import base64
import json

# M2M Client credentials
CLIENT_ID = "2ii86s6r14g9p4rrts9ajtjrhu"
CLIENT_SECRET = "1ls5730u8r2ohbdu0k7r08kog6ub041tivnbg0ud8q4j116tm2c0"
COGNITO_DOMAIN = "biops-038198578763.auth.us-east-1.amazoncognito.com"

def get_m2m_token():
    """Get access token using client credentials flow."""
    
    # Encode client credentials
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Token endpoint
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": "biops-api/read biops-api/write"
    }
    
    print(f"Requesting token from: {token_url}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Scopes: {data['scope']}")
    
    response = requests.post(token_url, headers=headers, data=data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        print(f"\nAccess Token: {access_token[:50]}...")
        return access_token
    else:
        print(f"Error getting token: {response.text}")
        return None

def test_api_with_token(access_token):
    """Test the API with the access token."""
    
    api_url = "https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod/jobs"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\nTesting API: {api_url}")
    response = requests.get(api_url, headers=headers)
    
    print(f"API Status: {response.status_code}")
    print(f"API Response: {response.text}")

if __name__ == "__main__":
    print("Testing Machine-to-Machine Authentication")
    print("=" * 50)
    
    # Get token
    token = get_m2m_token()
    
    if token:
        # Test API
        test_api_with_token(token)
    else:
        print("Failed to get access token")