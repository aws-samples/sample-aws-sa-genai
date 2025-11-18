import requests
import json
import time

# API Gateway endpoint
API_BASE_URL = "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod"

def start_job():
    """Start a new BIOPS deployment job."""
    config = {
        "source_account_id": "123456789012",
        "source_role_name": "QuickSightRole",
        "source_asset_id": "dashboard-id-123",
        "target_account_id": "210987654321",
        "target_role_name": "QuickSightRole",
        "target_admin_user": "admin-user",
        "bucket_name": "biops-version-control-demo-2025",
        "dashboard_name": "BIOpsDemo"
    }
    
    payload = {
        "config": config,
        "initiated_by": "user@example.com"
    }
    
    response = requests.post(f"{API_BASE_URL}/jobs", json=payload)
    print(f"Job started: {response.json()}")
    return response.json()

def get_job_status(job_id):
    """Get job status by ID."""
    response = requests.get(f"{API_BASE_URL}/jobs/{job_id}")
    return response.json()

def list_jobs():
    """List all jobs."""
    response = requests.get(f"{API_BASE_URL}/jobs")
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