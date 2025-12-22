import requests
import json
import time
import base64

# API Gateway endpoint
API_BASE_URL = "https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod" # Replace with your actual API Gateway URL

# OAuth credentials for machine-to-machine authentication
CLIENT_ID = "2ii86s6r14g9p4rrts9ajtjrhu"
CLIENT_SECRET = "1ls5730u8r2ohbdu0k7r08kog6ub041tivnbg0ud8q4j116tm2c0"
COGNITO_DOMAIN = "biops-038198578763.auth.us-east-1.amazoncognito.com"

def get_access_token():
    """Get access token for API authentication."""
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
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Failed to get token: {response.text}")
        return None

def get_auth_headers():
    """Get authorization headers for API requests."""
    token = get_access_token()
    if token:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return {"Content-Type": "application/json"} 

def start_job():
    """Start a new BIOPS deployment job."""
    config = {
        "source_account_id": "697957568932",
        "source_role_name": "BiopsSourceAccountRole",
        "source_asset_id": "1c39b477-2485-435c-be1e-23bc2b612304",
        "aws_region": "us-east-1",
        "target_account_id": "058421552426", #'210987654321'
        "target_role_name": "BiopsTargetAccountRole", #'QuickSightRole'
        "target_admin_user": "OrganizationAccountAccessRole/wangzyn-Isengard", #'admin-user'
        "bucket_name": "biops-version-control-demo-038198578763",
        "dashboard_name": "BIOpsDemo"
    }
    
    payload = {
        "config": config,
        "initiated_by": "user@example.com"
    }
    
    response = requests.post(f"{API_BASE_URL}/jobs", json=payload, headers=get_auth_headers())
    print(f"Job started: {response.json()}")
    return response.json()

def get_job_status(job_id):
    """Get job status by ID."""
    response = requests.get(f"{API_BASE_URL}/jobs/{job_id}", headers=get_auth_headers())
    return response.json()

def list_jobs():
    """List all jobs."""
    response = requests.get(f"{API_BASE_URL}/jobs", headers=get_auth_headers())
    return response.json()

def monitor_job(job_id, poll_interval=10):
    """Monitor job until completion."""
    while True:
        job = get_job_status(job_id)
        print(f"Job {job_id} status: {job.get('status', 'UNKNOWN')}")
        
        if job.get('status') in ['COMPLETED', 'FAILED']:
            print(f"Job finished with status: {job['status']}")
            if job.get('steps'):
                for step in job['steps']:
                    print(f"  Step {step['name']}: {step['status']}")
            break
        
        time.sleep(poll_interval)

if __name__ == "__main__":
    # Example usage
    print("Starting BIOPS deployment job...")
    result = start_job()
    
    # Monitor job (would need job_id from actual response)
    # job_id = "job-20251113-001"
    # monitor_job(job_id)
    
    # List all jobs
    print("\nAll jobs:")
    jobs = list_jobs()
    for job in jobs.get('jobs', []):
        print(f"  {job['jobId']}: {job['status']}")