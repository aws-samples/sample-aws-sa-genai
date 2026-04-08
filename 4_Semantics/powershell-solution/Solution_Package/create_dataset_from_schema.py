#!/usr/bin/env python3
"""
Create QuickSight Dataset from Generated Schema

This script demonstrates how to use the generated schema to create a QuickSight dataset.
"""

import boto3
import json
import os
import sys


def create_quicksight_dataset(schema_file: str, aws_profile: str = None, region: str = 'us-east-1'):
    """
    Create QuickSight dataset using the generated schema
    
    Args:
        schema_file: Path to the JSON schema file
        aws_profile: AWS profile name (optional)
        region: AWS region (default: us-east-1)
    """
    # Initialize AWS session
    if aws_profile:
        session = boto3.Session(profile_name=aws_profile)
    else:
        session = boto3.Session()
    
    # Initialize clients
    quicksight = session.client('quicksight', region_name=region)
    sts = session.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    print(f"Using AWS Account ID: {account_id}")
    print(f"Region: {region}")
    
    # Load schema
    with open(schema_file, 'r') as f:
        schema = json.load(f)
    
    dataset_id = schema['DataSetId']
    
    # Delete existing dataset if it exists
    try:
        quicksight.delete_data_set(
            AwsAccountId=account_id,
            DataSetId=dataset_id
        )
        print(f"Existing dataset deleted: {dataset_id}")
        import time
        time.sleep(5)  # Wait for deletion to complete
    except quicksight.exceptions.ResourceNotFoundException:
        print(f"No existing dataset found: {dataset_id}")
    except Exception as e:
        print(f"Warning: Could not delete existing dataset: {e}")
    
    # Create dataset
    try:
        response = quicksight.create_data_set(
            AwsAccountId=account_id,
            **schema
        )
        
        print(f"\n✓ Dataset created successfully!")
        print(f"Dataset ID: {response['DataSetId']}")
        print(f"Dataset ARN: {response['Arn']}")
        print(f"Status: {response['Status']}")
        
        # Create SPICE ingestion
        if schema.get('ImportMode') == 'SPICE':
            import time
            ingestion_id = f"ingestion-{int(time.time())}"
            ingestion_response = quicksight.create_ingestion(
                AwsAccountId=account_id,
                DataSetId=dataset_id,
                IngestionId=ingestion_id,
                IngestionType='FULL_REFRESH'
            )
            print(f"\n✓ SPICE ingestion started!")
            print(f"Ingestion ID: {ingestion_response['IngestionId']}")
            print(f"Ingestion Status: {ingestion_response['IngestionStatus']}")
        
        return response
        
    except Exception as e:
        print(f"\n✗ Error creating dataset: {e}")
        sys.exit(1)


def share_dataset_with_user(dataset_id: str, user_name: str, 
                           aws_profile: str = None, region: str = 'us-east-1'):
    """
    Share dataset with a specific QuickSight user
    
    Args:
        dataset_id: QuickSight dataset ID
        user_name: QuickSight user name (format: namespace/username or just username)
        aws_profile: AWS profile name (optional)
        region: AWS region (default: us-east-1)
    """
    # Initialize AWS session
    if aws_profile:
        session = boto3.Session(profile_name=aws_profile)
    else:
        session = boto3.Session()
    
    quicksight = session.client('quicksight', region_name=region)
    sts = session.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    # Validate user exists first
    try:
        # If user_name doesn't contain '/', try to find it
        if '/' not in user_name:
            print(f"  ⚠ User name '{user_name}' doesn't contain namespace. Searching for user...")
            users_response = quicksight.list_users(
                AwsAccountId=account_id,
                Namespace='default'
            )
            
            matching_users = [u for u in users_response['UserList'] if user_name in u['UserName']]
            if matching_users:
                user_name = matching_users[0]['UserName']
                print(f"  ✓ Found user: {user_name}")
            else:
                print(f"  ✗ User not found. Available users:")
                for user in users_response['UserList'][:10]:
                    print(f"    - {user['UserName']}")
                return None
        
        # Construct the principal ARN
        principal_arn = f"arn:aws:quicksight:{region}:{account_id}:user/default/{user_name}"
        
        response = quicksight.update_data_set_permissions(
            AwsAccountId=account_id,
            DataSetId=dataset_id,
            GrantPermissions=[
                {
                    'Principal': principal_arn,
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
        print(f"\n✓ Dataset shared with user: {user_name}")
        return response
        
    except quicksight.exceptions.ResourceNotFoundException as e:
        print(f"\n✗ User not found: {user_name}")
        print(f"  Error: {e}")
        print(f"\n  To list available users, run:")
        print(f"  aws quicksight list-users --aws-account-id {account_id} --namespace default --region {region}")
    except Exception as e:
        print(f"\n✗ Error sharing dataset: {e}")
        print(f"\n  Attempted to share with: {user_name}")
        print(f"  Principal ARN: arn:aws:quicksight:{region}:{account_id}:user/default/{user_name}")
        print(f"\n  To verify user exists, run:")
        print(f"  aws quicksight list-users --aws-account-id {account_id} --namespace default --region {region}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create QuickSight dataset from generated schema'
    )
    parser.add_argument(
        '--schema',
        default='quicksight_schema.json',
        help='Path to schema JSON file'
    )
    parser.add_argument(
        '--profile',
        help='AWS profile name (optional)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--share-with',
        help='QuickSight user to share with (format: namespace/username)'
    )
    
    args = parser.parse_args()
    
    # Create dataset
    response = create_quicksight_dataset(
        schema_file=args.schema,
        aws_profile=args.profile,
        region=args.region
    )
    
    # Share with user if specified
    if args.share_with:
        share_dataset_with_user(
            dataset_id=response['DataSetId'],
            user_name=args.share_with,
            aws_profile=args.profile,
            region=args.region
        )


if __name__ == '__main__':
    main()
