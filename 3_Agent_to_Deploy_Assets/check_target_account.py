#!/usr/bin/env python3
import boto3
import json

def check_target_account_dashboards():
    """Check dashboards in target account directly."""
    
    # Use target account profile directly
    session = boto3.Session(profile_name='target-account')  # Adjust profile name as needed
    quicksight_client = session.client('quicksight', region_name='us-east-1')
    
    target_account_id = "058421552426"
    
    try:
        print(f"=== Dashboards in Target Account {target_account_id} ===")
        dashboards = quicksight_client.list_dashboards(AwsAccountId=target_account_id)
        
        print(f"Found {len(dashboards.get('DashboardSummaryList', []))} dashboards:")
        
        for dashboard in dashboards.get('DashboardSummaryList', []):
            print(f"  📊 {dashboard['Name']}")
            print(f"     ID: {dashboard['DashboardId']}")
            print(f"     Created: {dashboard['CreatedTime']}")
            print(f"     Updated: {dashboard['LastUpdatedTime']}")
            print()
            
            # Check if this is our imported dashboard
            if 'BIOps' in dashboard['Name'] or dashboard['DashboardId'] == 'd41a3c00-e581-4ec2-969c-4778562bedd3':
                print(f"  ✅ Found imported dashboard: {dashboard['Name']}")
                
                # Get detailed info
                details = quicksight_client.describe_dashboard(
                    AwsAccountId=target_account_id,
                    DashboardId=dashboard['DashboardId']
                )
                
                print(f"     Status: {details['Dashboard']['Version']['Status']}")
                print(f"     Version: {details['Dashboard']['Version']['VersionNumber']}")
        
        # Also check datasets
        print(f"\n=== Datasets in Target Account ===")
        datasets = quicksight_client.list_data_sets(AwsAccountId=target_account_id)
        
        print(f"Found {len(datasets.get('DataSetSummaryList', []))} datasets:")
        for dataset in datasets.get('DataSetSummaryList', []):
            print(f"  📈 {dataset['Name']} (ID: {dataset['DataSetId']})")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Try using AWS CLI to check:")
        print(f"aws quicksight list-dashboards --aws-account-id {target_account_id} --region us-east-1")

if __name__ == "__main__":
    check_target_account_dashboards()