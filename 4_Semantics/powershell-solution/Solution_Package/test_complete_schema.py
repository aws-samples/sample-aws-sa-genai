#!/usr/bin/env python3
import boto3
import json
import time
import argparse

# Parse arguments
parser = argparse.ArgumentParser(description='Create QuickSight dataset and optionally share with users')
parser.add_argument('--profile', help='AWS profile name (optional)')
parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
parser.add_argument('--share-with', help='QuickSight username to share dataset with (format: namespace/username, e.g., Administrator/username)')
args = parser.parse_args()

# Load schema
with open('quicksight_schema_complete.json', 'r') as f:
    schema = json.load(f)

# Initialize AWS session
if args.profile:
    session = boto3.Session(profile_name=args.profile)
else:
    session = boto3.Session()

# Initialize QuickSight client
quicksight = session.client('quicksight', region_name=args.region)
sts = session.client('sts')
account_id = sts.get_caller_identity()['Account']

print(f'Account: {account_id}')
print(f'Dataset ID: {schema["DataSetId"]}')

# Delete existing if exists
try:
    quicksight.delete_data_set(
        AwsAccountId=account_id,
        DataSetId=schema['DataSetId']
    )
    print('Deleted existing dataset')
    time.sleep(5)
except:
    print('No existing dataset')

# Create dataset
try:
    response = quicksight.create_data_set(
        AwsAccountId=account_id,
        **schema
    )
    print(f'✓ Dataset created: {response["DataSetId"]}')
    print(f'✓ Status: {response["Status"]}')
    
    # Start SPICE ingestion
    ingestion_id = f"ingestion-{int(time.time())}"
    ing_response = quicksight.create_ingestion(
        AwsAccountId=account_id,
        DataSetId=schema['DataSetId'],
        IngestionId=ingestion_id,
        IngestionType='FULL_REFRESH'
    )
    print(f'✓ Ingestion started: {ing_response["IngestionId"]}')
    
    # Share dataset with user if specified
    if args.share_with:
        try:
            # The share-with format should be: namespace/username
            # But in QuickSight, the actual UserName in the API might already include namespace
            # e.g., "Administrator/wangzyn-Isengard" is the full UserName
            
            # First, try to use it as-is (full username with namespace prefix)
            try:
                user_response = quicksight.describe_user(
                    AwsAccountId=account_id,
                    Namespace='default',  # Users are in the default namespace
                    UserName=args.share_with
                )
                user_arn = user_response['User']['Arn']
                username_display = args.share_with
            except:
                # If that fails, try parsing it
                if '/' in args.share_with:
                    namespace, username = args.share_with.split('/', 1)
                else:
                    namespace = 'default'
                    username = args.share_with
                
                user_response = quicksight.describe_user(
                    AwsAccountId=account_id,
                    Namespace=namespace,
                    UserName=username
                )
                user_arn = user_response['User']['Arn']
                username_display = f'{namespace}/{username}'
            
            # Update dataset permissions - grant full permissions
            permissions_response = quicksight.update_data_set_permissions(
                AwsAccountId=account_id,
                DataSetId=schema['DataSetId'],
                GrantPermissions=[
                    {
                        'Principal': user_arn,
                        'Actions': [
                            'quicksight:UpdateDataSetPermissions',
                            'quicksight:DescribeDataSet',
                            'quicksight:DescribeDataSetPermissions',
                            'quicksight:PassDataSet',
                            'quicksight:DescribeIngestion',
                            'quicksight:ListIngestions',
                            'quicksight:UpdateDataSet',
                            'quicksight:DeleteDataSet',
                            'quicksight:CreateIngestion',
                            'quicksight:CancelIngestion'
                        ]
                    }
                ]
            )
            print(f'✓ Dataset shared with: {username_display}')
            print(f'  User ARN: {user_arn}')
            
        except Exception as e:
            print(f'✗ Error sharing dataset: {e}')
    
except Exception as e:
    print(f'✗ Error: {e}')
