#!/usr/bin/env python3
"""
Create QuickSight Snowflake Data Source

This script creates a QuickSight data source for Snowflake using credentials
stored in AWS Secrets Manager.
"""

import boto3
import json
import sys


def get_secret(secret_name: str, region: str = 'us-east-1'):
    """
    Retrieve secret from AWS Secrets Manager
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        region: AWS region (default: us-east-1)
    
    Returns:
        Dictionary containing the secret values
    """
    client = boto3.client('secretsmanager', region_name=region)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error retrieving secret '{secret_name}': {e}")
        sys.exit(1)


def create_snowflake_datasource(
    datasource_id: str,
    datasource_name: str,
    secret_name: str,
    aws_profile: str = None,
    region: str = 'us-east-1',
    delete_existing: bool = True
):
    """
    Create QuickSight Snowflake data source
    
    Args:
        datasource_id: QuickSight data source ID
        datasource_name: Display name for the data source
        secret_name: AWS Secrets Manager secret name containing Snowflake credentials
        aws_profile: AWS profile name (optional)
        region: AWS region (default: us-east-1)
        delete_existing: Whether to delete existing data source with same ID
    
    Expected secret format:
    {
        "account": "your-snowflake-account",
        "database": "DATABASE_NAME",
        "warehouse": "WAREHOUSE_NAME",
        "user": "USERNAME",
        "password": "PASSWORD"
    }
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
    print(f"Region: {region}\n")
    
    # Get Snowflake credentials from Secrets Manager
    print(f"Retrieving Snowflake credentials from secret: {secret_name}")
    snowflake_config = get_secret(secret_name, region)
    
    # Validate required fields
    required_fields = ['account', 'database', 'warehouse', 'user', 'password']
    missing_fields = [field for field in required_fields if field not in snowflake_config]
    
    if missing_fields:
        print(f"✗ Error: Secret is missing required fields: {', '.join(missing_fields)}")
        print(f"\nExpected secret format:")
        print(json.dumps({
            "account": "your-snowflake-account",
            "database": "DATABASE_NAME",
            "warehouse": "WAREHOUSE_NAME",
            "user": "USERNAME",
            "password": "PASSWORD"
        }, indent=2))
        sys.exit(1)
    
    print(f"  ✓ Snowflake Account: {snowflake_config['account']}")
    print(f"  ✓ Database: {snowflake_config['database']}")
    print(f"  ✓ Warehouse: {snowflake_config['warehouse']}")
    print(f"  ✓ User: {snowflake_config['user']}\n")
    
    # Delete existing data source if requested
    if delete_existing:
        print(f"Checking for existing data source: {datasource_id}")
        try:
            quicksight.delete_data_source(
                AwsAccountId=account_id,
                DataSourceId=datasource_id
            )
            print(f"  ✓ Deleted existing data source\n")
            import time
            time.sleep(3)  # Wait for deletion to complete
        except quicksight.exceptions.ResourceNotFoundException:
            print(f"  ✓ No existing data source found\n")
        except Exception as e:
            print(f"  ⚠ Warning: Could not delete existing data source: {e}\n")
    
    # Create Snowflake data source
    print(f"Creating Snowflake data source: {datasource_name}")
    
    try:
        response = quicksight.create_data_source(
            AwsAccountId=account_id,
            DataSourceId=datasource_id,
            Name=datasource_name,
            Type='SNOWFLAKE',
            DataSourceParameters={
                'SnowflakeParameters': {
                    'Host': f"{snowflake_config['account']}.snowflakecomputing.com",
                    'Database': snowflake_config['database'],
                    'Warehouse': snowflake_config['warehouse']
                }
            },
            Credentials={
                'CredentialPair': {
                    'Username': snowflake_config['user'],
                    'Password': snowflake_config['password']
                }
            },
            # Optional: Add VPC connection if needed
            # VpcConnectionProperties={
            #     'VpcConnectionArn': 'arn:aws:quicksight:region:account:vpcConnection/vpc-id'
            # }
        )
        
        print(f"\n{'='*60}")
        print(f"✓ Data Source Created Successfully!")
        print(f"{'='*60}")
        print(f"\nData Source Details:")
        print(f"  ID: {response['DataSourceId']}")
        print(f"  ARN: {response['Arn']}")
        print(f"  Status: {response['Status']}")
        print(f"  Creation Status: {response.get('CreationStatus', 'N/A')}")
        
        return response
        
    except Exception as e:
        print(f"\n✗ Error creating data source: {e}")
        sys.exit(1)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create QuickSight Snowflake data source using AWS Secrets Manager'
    )
    parser.add_argument(
        '--datasource-id',
        default='movies-snowflake-datasource',
        help='QuickSight data source ID (default: movies-snowflake-datasource)'
    )
    parser.add_argument(
        '--datasource-name',
        default='Movies Snowflake Data Source',
        help='Display name for the data source (default: Movies Snowflake Data Source)'
    )
    parser.add_argument(
        '--secret-name',
        required=True,
        help='AWS Secrets Manager secret name containing Snowflake credentials (required)'
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
        '--no-delete',
        action='store_true',
        help='Do not delete existing data source with same ID'
    )
    
    args = parser.parse_args()
    
    # Create data source
    response = create_snowflake_datasource(
        datasource_id=args.datasource_id,
        datasource_name=args.datasource_name,
        secret_name=args.secret_name,
        aws_profile=args.profile,
        region=args.region,
        delete_existing=not args.no_delete
    )
    
    print(f"\nNext Steps:")
    print(f"1. Use this data source ARN in generate_quicksight_schema.py:")
    print(f"   --datasource-arn \"{response['Arn']}\"")
    print(f"\n2. Or reference by ID when creating datasets:")
    print(f"   DataSourceId: {response['DataSourceId']}")


if __name__ == '__main__':
    main()
