#!/usr/bin/env python3
"""
Validation script to check if all prerequisites are met

This script validates:
1. AWS credentials are configured
2. Required Python packages are installed
3. AWS Secrets Manager secret exists (optional)
4. QuickSight data source exists (optional)
5. CSV file exists and is readable
"""

import sys
import os


def check_python_packages():
    """Check if required Python packages are installed"""
    print("Checking Python packages...")
    required_packages = ['boto3']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package} is installed")
        except ImportError:
            print(f"  ✗ {package} is NOT installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstall missing packages:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    
    return True


def check_aws_credentials(profile=None):
    """Check if AWS credentials are configured"""
    print("\nChecking AWS credentials...")
    
    try:
        import boto3
        
        if profile:
            session = boto3.Session(profile_name=profile)
        else:
            session = boto3.Session()
        
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"  ✓ AWS credentials are configured")
        print(f"    Account ID: {identity['Account']}")
        print(f"    User ARN: {identity['Arn']}")
        return True
        
    except Exception as e:
        print(f"  ✗ AWS credentials are NOT configured: {e}")
        return False


def check_secret(secret_name, region='us-east-1', profile=None):
    """Check if AWS Secrets Manager secret exists"""
    print(f"\nChecking AWS Secrets Manager secret: {secret_name}")
    
    try:
        import boto3
        
        if profile:
            session = boto3.Session(profile_name=profile)
        else:
            session = boto3.Session()
        
        client = session.client('secretsmanager', region_name=region)
        response = client.describe_secret(SecretId=secret_name)
        
        print(f"  ✓ Secret exists: {secret_name}")
        print(f"    ARN: {response['ARN']}")
        
        # Try to get the secret value
        secret_value = client.get_secret_value(SecretId=secret_name)
        import json
        secret_data = json.loads(secret_value['SecretString'])
        
        required_fields = ['account', 'database', 'warehouse', 'user', 'password']
        missing_fields = [f for f in required_fields if f not in secret_data]
        
        if missing_fields:
            print(f"  ⚠ Secret is missing required fields: {', '.join(missing_fields)}")
            return False
        
        print(f"    Account: {secret_data.get('account')}")
        print(f"    Database: {secret_data.get('database')}")
        print(f"    Warehouse: {secret_data.get('warehouse')}")
        print(f"    User: {secret_data.get('user')}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Secret not found or not accessible: {e}")
        print(f"    Run: ./setup_secrets.sh to create it")
        return False


def check_datasource(datasource_id, region='us-east-1', profile=None):
    """Check if QuickSight data source exists"""
    print(f"\nChecking QuickSight data source: {datasource_id}")
    
    try:
        import boto3
        
        if profile:
            session = boto3.Session(profile_name=profile)
        else:
            session = boto3.Session()
        
        quicksight = session.client('quicksight', region_name=region)
        sts = session.client('sts')
        account_id = sts.get_caller_identity()['Account']
        
        response = quicksight.describe_data_source(
            AwsAccountId=account_id,
            DataSourceId=datasource_id
        )
        
        datasource = response['DataSource']
        print(f"  ✓ Data source exists: {datasource_id}")
        print(f"    ARN: {datasource['Arn']}")
        print(f"    Type: {datasource['Type']}")
        print(f"    Status: {datasource.get('Status', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Data source not found: {e}")
        print(f"    Run: python create_snowflake_datasource.py to create it")
        return False


def check_csv_file(csv_path):
    """Check if CSV file exists and is readable"""
    print(f"\nChecking CSV file: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"  ✗ CSV file does not exist")
        return False
    
    try:
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            print(f"  ✓ CSV file exists and is readable")
            print(f"    Lines: {len(lines)}")
        return True
    except Exception as e:
        print(f"  ✗ Cannot read CSV file: {e}")
        return False


def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate setup for QuickSight dataset creation'
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
        '--secret-name',
        default='snowflake-credentials',
        help='AWS Secrets Manager secret name (default: snowflake-credentials)'
    )
    parser.add_argument(
        '--datasource-id',
        default='movies-snowflake-datasource',
        help='QuickSight data source ID (default: movies-snowflake-datasource)'
    )
    parser.add_argument(
        '--csv-path',
        default='/Users/wangzyn/snowflake-quicksight-workshop/quick_start/SF_DDL.csv',
        help='Path to Snowflake DDL CSV file'
    )
    parser.add_argument(
        '--skip-optional',
        action='store_true',
        help='Skip optional checks (secret and data source)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("QuickSight Dataset Creation - Setup Validation")
    print("="*60)
    
    results = []
    
    # Required checks
    results.append(("Python packages", check_python_packages()))
    results.append(("AWS credentials", check_aws_credentials(args.profile)))
    results.append(("CSV file", check_csv_file(args.csv_path)))
    
    # Optional checks
    if not args.skip_optional:
        results.append(("Secrets Manager secret", check_secret(
            args.secret_name, args.region, args.profile
        )))
        results.append(("QuickSight data source", check_datasource(
            args.datasource_id, args.region, args.profile
        )))
    
    # Summary
    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! You're ready to create QuickSight datasets.")
        print("\nNext steps:")
        print("1. python generate_quicksight_schema.py --datasource-arn <ARN>")
        print("2. python create_dataset_from_schema.py --schema quicksight_schema.json")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
