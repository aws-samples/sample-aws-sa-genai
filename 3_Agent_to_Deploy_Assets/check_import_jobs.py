#!/usr/bin/env python3
import boto3
import json

def check_import_jobs():
    """Check QuickSight import jobs in target account using cross-account role."""
    
    # Assume role in target account from tools account
    session = boto3.Session(profile_name='tools-account')
    sts_client = session.client('sts', region_name='us-east-1')
    
    target_account_id = "058421552426"
    role_arn = f"arn:aws:iam::{target_account_id}:role/BiopsTargetAccountRole"
    
    try:
        # Assume the target account role
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="BiopsImportCheck"
        )
        
        credentials = assumed_role['Credentials']
        quicksight_client = boto3.client(
            'quicksight',
            region_name='us-east-1',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        
        print(f"✅ Successfully assumed role in target account {target_account_id}")
        
        # List asset bundle import jobs
        print("\n=== Asset Bundle Import Jobs ===")
        import_jobs = quicksight_client.list_asset_bundle_import_jobs(
            AwsAccountId=target_account_id
        )
        
        if import_jobs.get('AssetBundleImportJobSummaryList'):
            for job in import_jobs['AssetBundleImportJobSummaryList']:
                print(f"Job ID: {job['JobId']}")
                print(f"Status: {job['JobStatus']}")
                print(f"Created: {job['CreatedTime']}")
                
                # Get detailed job info
                job_details = quicksight_client.describe_asset_bundle_import_job(
                    AwsAccountId=target_account_id,
                    AssetBundleImportJobId=job['JobId']
                )
                
                print(f"Assets Created: {len(job_details.get('AssetBundleImportJobSummary', {}).get('AssetBundleImportJobSummary', {}).get('CreatedAssets', []))}")
                
                if job_details.get('Errors'):
                    print(f"Errors: {job_details['Errors']}")
                
                print("-" * 50)
        else:
            print("No import jobs found")
            
        # Also list dashboards to see what exists
        print("\n=== Current Dashboards ===")
        dashboards = quicksight_client.list_dashboards(AwsAccountId=target_account_id)
        
        for dashboard in dashboards.get('DashboardSummaryList', []):
            print(f"📊 {dashboard['Name']} (ID: {dashboard['DashboardId']})")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def check_recent_lambda_logs():
    """Check recent Lambda import function logs."""
    
    session = boto3.Session(profile_name='tools-account')
    logs_client = session.client('logs', region_name='us-east-1')
    
    log_group = "/aws/lambda/biops-import-assets"
    
    try:
        # Get recent log streams
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        print(f"\n=== Recent Import Lambda Logs ===")
        
        for stream in streams['logStreams']:
            print(f"\nLog Stream: {stream['logStreamName']}")
            print(f"Last Event: {stream.get('lastEventTime', 'N/A')}")
            
            # Get log events
            events = logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=stream['logStreamName'],
                limit=10
            )
            
            for event in events['events']:
                if 'SUCCESSFUL' in event['message'] or 'FAILED' in event['message'] or 'ERROR' in event['message']:
                    print(f"  {event['message']}")
                    
    except Exception as e:
        print(f"❌ Error checking logs: {str(e)}")

if __name__ == "__main__":
    print("BIOPS Import Job Verification")
    print("=" * 50)
    
    check_import_jobs()
    check_recent_lambda_logs()