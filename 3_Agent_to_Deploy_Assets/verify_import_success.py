#!/usr/bin/env python3
import boto3
import json

def verify_import_success():
    """Verify that the QuickSight dashboard was successfully imported to target account."""
    
    # Target account details
    target_account_id = "058421552426"
    target_role_name = "BiopsTargetAccountRole"
    dashboard_name = "BIOpsDemo"
    region = "us-east-1"
    
    # Assume role in target account
    sts_client = boto3.client('sts', region_name=region)
    role_arn = f"arn:aws:iam::{target_account_id}:role/{target_role_name}"
    
    try:
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="BiopsVerification"
        )
        
        # Create QuickSight client with assumed role credentials
        credentials = assumed_role['Credentials']
        quicksight_client = boto3.client(
            'quicksight',
            region_name=region,
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        
        print(f"✓ Successfully assumed role in target account {target_account_id}")
        
        # List all dashboards in target account
        print("\n=== Dashboards in Target Account ===")
        dashboards = quicksight_client.list_dashboards(AwsAccountId=target_account_id)
        
        found_dashboard = False
        for dashboard in dashboards.get('DashboardSummaryList', []):
            print(f"Dashboard: {dashboard['Name']} (ID: {dashboard['DashboardId']})")
            if dashboard['Name'] == dashboard_name:
                found_dashboard = True
                dashboard_id = dashboard['DashboardId']
                
                # Get detailed dashboard info
                dashboard_details = quicksight_client.describe_dashboard(
                    AwsAccountId=target_account_id,
                    DashboardId=dashboard_id
                )
                
                print(f"\n✓ Found imported dashboard: {dashboard_name}")
                print(f"  Dashboard ID: {dashboard_id}")
                print(f"  Status: {dashboard_details['Dashboard']['Version']['Status']}")
                print(f"  Created: {dashboard_details['Dashboard']['CreatedTime']}")
                print(f"  Last Updated: {dashboard_details['Dashboard']['LastUpdatedTime']}")
                
                # Check permissions
                try:
                    permissions = quicksight_client.describe_dashboard_permissions(
                        AwsAccountId=target_account_id,
                        DashboardId=dashboard_id
                    )
                    print(f"  Permissions: {len(permissions['Permissions'])} entries")
                    for perm in permissions['Permissions']:
                        print(f"    - {perm['Principal']}: {perm['Actions']}")
                except Exception as e:
                    print(f"  Could not retrieve permissions: {e}")
        
        if not found_dashboard:
            print(f"❌ Dashboard '{dashboard_name}' not found in target account")
            return False
        
        # List datasets to verify they were imported too
        print(f"\n=== Datasets in Target Account ===")
        datasets = quicksight_client.list_data_sets(AwsAccountId=target_account_id)
        
        for dataset in datasets.get('DataSetSummaryList', []):
            print(f"Dataset: {dataset['Name']} (ID: {dataset['DataSetId']})")
        
        print(f"\n✅ Import verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying import: {str(e)}")
        return False

def check_s3_artifacts():
    """Check S3 bucket for import artifacts."""
    
    session = boto3.Session(profile_name='tools-account')
    s3_client = session.client('s3', region_name='us-east-1')
    bucket_name = "biops-version-control-demo-038198578763"
    
    print(f"\n=== S3 Artifacts in {bucket_name} ===")
    
    try:
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in objects:
            for obj in objects['Contents']:
                print(f"  {obj['Key']} ({obj['Size']} bytes, {obj['LastModified']})")
        else:
            print("  No objects found in bucket")
            
    except Exception as e:
        print(f"❌ Error checking S3: {str(e)}")

if __name__ == "__main__":
    print("BIOPS Import Verification")
    print("=" * 50)
    
    # Check S3 artifacts first
    check_s3_artifacts()
    
    # Verify import in target account
    success = verify_import_success()
    
    if success:
        print("\n🎉 Import verification PASSED - Dashboard successfully imported!")
    else:
        print("\n💥 Import verification FAILED - Check logs for details")