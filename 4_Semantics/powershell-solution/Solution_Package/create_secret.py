#!/usr/bin/env python3
"""
Create or update AWS Secrets Manager secret for Snowflake credentials

Non-interactive version that can be run with command-line arguments.
"""

import boto3
import json
import sys


def create_or_update_secret(
    secret_name: str,
    account: str,
    database: str,
    warehouse: str,
    user: str,
    password: str,
    region: str = 'us-east-1',
    profile: str = None
):
    """
    Create or update AWS Secrets Manager secret
    
    Args:
        secret_name: Name of the secret
        account: Snowflake account identifier
        database: Snowflake database name
        warehouse: Snowflake warehouse name
        user: Snowflake username
        password: Snowflake password
        region: AWS region
        profile: AWS profile name (optional)
    """
    # Initialize AWS session
    if profile:
        session = boto3.Session(profile_name=profile)
    else:
        session = boto3.Session()
    
    client = session.client('secretsmanager', region_name=region)
    
    # Create secret JSON
    secret_data = {
        'account': account,
        'database': database,
        'warehouse': warehouse,
        'user': user,
        'password': password
    }
    
    secret_string = json.dumps(secret_data)
    
    print(f"Creating/updating secret: {secret_name}")
    print(f"Region: {region}")
    print(f"Account: {account}")
    print(f"Database: {database}")
    print(f"Warehouse: {warehouse}")
    print(f"User: {user}")
    print()
    
    # Check if secret exists
    try:
        client.describe_secret(SecretId=secret_name)
        print(f"Secret '{secret_name}' already exists. Updating...")
        
        response = client.update_secret(
            SecretId=secret_name,
            SecretString=secret_string
        )
        
        print(f"✓ Secret updated successfully!")
        print(f"  ARN: {response['ARN']}")
        print(f"  Version ID: {response['VersionId']}")
        
    except client.exceptions.ResourceNotFoundException:
        print(f"Creating new secret '{secret_name}'...")
        
        response = client.create_secret(
            Name=secret_name,
            Description='Snowflake credentials for QuickSight data source',
            SecretString=secret_string
        )
        
        print(f"✓ Secret created successfully!")
        print(f"  ARN: {response['ARN']}")
        print(f"  Version ID: {response['VersionId']}")
    
    print()
    print("Next Steps:")
    print(f"1. Create QuickSight data source:")
    print(f"   python create_snowflake_datasource.py --secret-name {secret_name}")
    print()
    print(f"2. Verify the secret:")
    print(f"   aws secretsmanager get-secret-value --secret-id {secret_name} --region {region}")
    
    return response


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create or update AWS Secrets Manager secret for Snowflake credentials'
    )
    parser.add_argument(
        '--secret-name',
        default='snowflake-credentials',
        help='Name of the secret (default: snowflake-credentials)'
    )
    parser.add_argument(
        '--account',
        required=True,
        help='Snowflake account identifier (required)'
    )
    parser.add_argument(
        '--database',
        default='MOVIES',
        help='Snowflake database name (default: MOVIES)'
    )
    parser.add_argument(
        '--warehouse',
        default='WORKSHOPWH',
        help='Snowflake warehouse name (default: WORKSHOPWH)'
    )
    parser.add_argument(
        '--user',
        required=True,
        help='Snowflake username (required)'
    )
    parser.add_argument(
        '--password',
        required=True,
        help='Snowflake password (required)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--profile',
        help='AWS profile name (optional)'
    )
    
    args = parser.parse_args()
    
    try:
        create_or_update_secret(
            secret_name=args.secret_name,
            account=args.account,
            database=args.database,
            warehouse=args.warehouse,
            user=args.user,
            password=args.password,
            region=args.region,
            profile=args.profile
        )
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
