import requests
import base64
import json

def test_token_endpoint():
    """Test the Cognito token endpoint that QuickSight uses."""
    
    # QuickSight client credentials (new dedicated client)
    client_id = "13m1ionmfagtidvo094r90lq4a"
    client_secret = "1vjeuqjftl6svdj5vnm31kh8o9lei539n3sb9eq8mi266reik5sl"
    token_url = "https://biops-038198578763.auth.us-east-1.amazoncognito.com/oauth2/token"
    
    # Create Basic Auth header
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    # Test different grant types
    print("🧪 Testing token endpoint...")
    
    # Test 1: Client credentials (should work for API access)
    print("\n1. Testing client_credentials grant...")
    data = {
        "grant_type": "client_credentials",
        "scope": "biops-api/read biops-api/write"
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 2: Authorization code (what QuickSight needs)
    print("\n2. Testing authorization_code grant (simulated)...")
    data = {
        "grant_type": "authorization_code",
        "code": "dummy_code",  # This will fail but shows the endpoint response
        "redirect_uri": "https://us-east-1.quicksight.aws.amazon.com/sn/oauthcallback"
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 3: Check if endpoint supports PKCE
    print("\n3. Testing PKCE parameters...")
    data = {
        "grant_type": "authorization_code",
        "code": "dummy_code",
        "redirect_uri": "https://us-east-1.quicksight.aws.amazon.com/sn/oauthcallback",
        "code_verifier": "dummy_verifier"
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

def check_user_info_endpoint():
    """Test the user info endpoint."""
    print("\n🔍 Testing user info endpoint...")
    
    # This would need a valid access token
    user_info_url = "https://biops-038198578763.auth.us-east-1.amazoncognito.com/oauth2/userInfo"
    
    headers = {
        "Authorization": "Bearer dummy_token"
    }
    
    response = requests.get(user_info_url, headers=headers)
    print(f"User Info Status: {response.status_code}")
    print(f"User Info Response: {response.text}")

if __name__ == "__main__":
    test_token_endpoint()
    check_user_info_endpoint()
    
    print("\n" + "="*50)
    print("🔧 DIAGNOSIS:")
    print("QuickSight can discover your API but cannot get access tokens.")
    print("This suggests the OAuth token exchange is failing.")
    print("Check if QuickSight needs specific token endpoint configuration.")