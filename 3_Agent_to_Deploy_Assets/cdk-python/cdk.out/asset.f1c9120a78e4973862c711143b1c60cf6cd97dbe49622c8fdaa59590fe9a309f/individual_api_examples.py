import requests
import json
import time

API_BASE_URL = "https://1cv3q605h2.execute-api.us-east-1.amazonaws.com/prod" # Tools account API Gateway URL

def start_export_job():
    """Start QuickSight asset export job."""
    payload = {
        "source_account_id": "499080683179",
        "source_role_name": "BiopsSourceAccountRole",
        "source_asset_id": "d41a3c00-e581-4ec2-969c-4778562bedd3",
        "aws_region": "us-east-1"
    }
    
    response = requests.post(f"{API_BASE_URL}/export", json=payload)
    print(f"Export started: {response.json()}")
    return response.json()

def check_export_status(export_job_id):
    """Check export job status."""
    payload = {
        "source_account_id": "499080683179",
        "source_role_name": "BiopsSourceAccountRole",
        "aws_region": "us-east-1"
    }
    
    response = requests.get(f"{API_BASE_URL}/export/{export_job_id}", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200 and response.text:
        return response.json()
    else:
        return {"error": f"API returned status {response.status_code}: {response.text}"}

def upload_assets():
    """Upload exported assets to S3."""
    payload = {
        "download_url": "https://quicksight-export-url...",
        "job_id": "export-job-123",
        "export_format": "QUICKSIGHT_JSON",
        "bucket_name": "biops-version-control-demo-038198578763",
        "aws_region": "us-east-1"
    }
    
    response = requests.post(f"{API_BASE_URL}/upload", json=payload)
    print(f"Upload result: {response.json()}")
    return response.json()

def import_assets():
    """Import assets from S3 to target account."""
    payload = {
        "s3_uri": "s3://biops-version-control-demo-038198578763/QUICKSIGHT_JSON_d41a3c00-e581-4ec2-969c-4778562bedd3_499080683179_2025-11-17/QUICKSIGHT_JSON_d41a3c00-e581-4ec2-969c-4778562bedd3_499080683179_2025-11-17.qs",
        "source_asset_id": "d41a3c00-e581-4ec2-969c-4778562bedd3",
        "target_account_id": "058421552426",
        "target_role_name": "BiopsTargetAccountRole",
        "aws_region": "us-east-1"
    }
    
    response = requests.post(f"{API_BASE_URL}/import", json=payload)
    print(f"Import result: {response.json()}")
    return response.json()

def check_import_status(import_job_id):
    """Check import job status."""
    payload = {
        "target_account_id": "058421552426",
        "target_role_name": "BiopsTargetAccountRole",
        "aws_region": "us-east-1"
    }
    
    response = requests.get(f"{API_BASE_URL}/import/{import_job_id}", json=payload)
    return response.json()

def update_permissions():
    """Update permissions for imported assets."""
    payload = {
        "dashboard_name": "BIOpsDemo",
        "target_account_id": "058421552426",
        "target_role_name": "BiopsTargetAccountRole",
        "target_admin_user": "admin",
        "aws_region": "us-east-1"
    }
    
    response = requests.post(f"{API_BASE_URL}/permissions", json=payload)
    print(f"Permissions updated: {response.json()}")
    return response.json()

def full_workflow_example():
    """Example of complete workflow using individual APIs."""
    print("=== BIOPS Individual API Workflow ===")
    
    # Step 1: Start export
    print("1. Starting export...")
    export_result = start_export_job()
    export_job_id = export_result.get('job_id')
    
    # Step 2: Wait for export completion
    print("2. Waiting for export completion...")
    while True:
        status = check_export_status(export_job_id)
        if status.get('JobStatus') == 'SUCCESSFUL':
            download_url = status.get('DownloadUrl')
            break
        elif status.get('JobStatus') == 'FAILED':
            print("Export failed!")
            return
        time.sleep(10)
    
    # Step 3: Upload to S3
    print("3. Uploading to S3...")
    upload_result = upload_assets()
    s3_uri = upload_result.get('s3_uri')
    
    # Step 4: Import assets
    print("4. Importing assets...")
    import_result = import_assets()
    import_job_id = import_result.get('job_id')
    
    # Step 5: Wait for import completion
    print("5. Waiting for import completion...")
    while True:
        status = check_import_status(import_job_id)
        if status.get('status') == 'SUCCESSFUL':
            print("Import completed successfully!")
            break
        elif status.get('status') == 'FAILED':
            print("Import failed!")
            return
        time.sleep(10)
    
    # Step 6: Update permissions
    print("6. Updating permissions...")
    permissions_result = update_permissions()
    
    print("Workflow completed successfully!")

if __name__ == "__main__":
    # Individual API examples
    print("Individual API Usage Examples:")
    print("1. start_export_job()")
    print("2. check_export_status('job-id')")
    print("3. upload_assets()")
    print("4. import_assets()")
    print("5. check_import_status('import-job-id')")
    print("6. update_permissions()")
    print("\nRun full_workflow_example() for complete flow")

    # Example: Export and then upload with extracted download_url
    print("\n=== Export and Upload Example ===")
    
    # Step 1: Start export job
    """
    export_result = start_export_job()
    
    if export_result:
        # Extract values from export result
        download_url = export_result.get('download_url')
        job_id = export_result.get('job_id')
        export_format = export_result.get('export_format')
        
        print(f"\nExtracted values:")
        print(f"Job ID: {job_id}")
        print(f"Export Format: {export_format}")
        print(f"Download URL: {download_url[:100]}...")
        
        # Step 2: Upload with extracted values
        if download_url:
            upload_payload = {
                "download_url": download_url,
                "job_id": job_id,
                "export_format": export_format,
                "bucket_name": "biops-version-control-demo-038198578763",
                "aws_region": "us-east-1"
            }
            
            print(f"\nUploading with extracted values...")
            response = requests.post(f"{API_BASE_URL}/upload", json=upload_payload)
            print(f"Upload result: {response.json()}")
    """
    # Uncomment to test other functions:
    # result = full_workflow_example()
    # result = import_assets()
    # result = update_permissions()
    result = check_export_status('d41a3c00-e581-4ec2-969c-4778562bedd3_499080683179_2025-11-17')