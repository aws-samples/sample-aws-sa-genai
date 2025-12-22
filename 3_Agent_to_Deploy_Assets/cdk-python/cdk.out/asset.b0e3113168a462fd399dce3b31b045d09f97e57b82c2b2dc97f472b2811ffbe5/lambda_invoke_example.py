import json
import boto3

def deploy_assets_example():
    """Example usage of the BIOPS asset deployment Lambda functions."""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Configuration for asset deployment
    config = {
        "source_account_id": "499080683179", #'123456789012'
        "source_role_name": "BiopsSourceAccountRole", # 'QuickSightRole'
        "source_asset_id": "d41a3c00-e581-4ec2-969c-4778562bedd3", #'dashboard-id-123'
        "target_account_id": "058421552426", #'210987654321'
        "target_role_name": "BiopsTargetAccountRole", #'QuickSightRole'
        "target_admin_user": "OrganizationAccountAccessRole/wangzyn-Isengard", #'admin-user'
        "bucket_name": "biops-version-control-demo-038198578763", #'biops-version-control-demo-2025'
        "dashboard_name": "BIOpsDemo", # 'MyDashboard'
        "aws_region": "us-east-1"
    }
    
    # Call orchestrator function
    response = lambda_client.invoke(
        FunctionName='biops-orchestrator',
        InvocationType='RequestResponse',
        Payload=json.dumps({'config': config})
    )
    
    result = json.loads(response['Payload'].read())
    print(json.dumps(result, indent=2))
    
    return result

def deploy_individual_steps(function_name, payload):
    """Invoke individual Lambda function with custom payload."""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"{function_name} Result:", json.dumps(result, indent=2))
        return result
        
    except Exception as e:
        print(f"Error invoking {function_name}: {str(e)}")
        return None

def example_payloads():
    """Return example payloads for each Lambda function."""
    return {
        'biops-export-assets': {
            'source_account_id': '499080683179', #'123456789012'
            'source_role_name': 'BiopsSourceAccountRole', # 'QuickSightRole'
            'source_asset_id': 'd41a3c00-e581-4ec2-969c-4778562bedd3', #'dashboard-id-123'
            'aws_region': 'us-east-1'
        },
        'biops-upload-assets': {
            'download_url': 'https://quicksight-export-url...',
            'job_id': 'export-job-123',
            'export_format': 'QUICKSIGHT_JSON',
            'bucket_name': 'biops-version-control-demo-038198578763',
            'aws_region': 'us-east-1'
        },
        'biops-import-assets': {
            's3_uri': 's3://biops-version-control-demo-038198578763/QUICKSIGHT_JSON_d41a3c00-e581-4ec2-969c-4778562bedd3_499080683179_2025-11-17/QUICKSIGHT_JSON_d41a3c00-e581-4ec2-969c-4778562bedd3_499080683179_2025-11-17.qs', # 's3://bucket/path/bundle.zip' Example S3 URI
            'source_asset_id': 'd41a3c00-e581-4ec2-969c-4778562bedd3',# 'dashboard-id-123'
            'target_account_id': '058421552426', #'210987654321'
            'target_role_name': 'BiopsTargetAccountRole', #'QuickSightRole'
            'aws_region': 'us-east-1'
        },
        'biops-update-permissions': {
            'dashboard_name': 'BIOpsDemo', # 'MyDashboard'
            'target_account_id': '058421552426', # '210987654321'
            'target_role_name': 'BiopsTargetAccountRole', # 'QuickSightRole'
            'target_admin_user': 'OrganizationAccountAccessRole/wangzyn-Isengard', # 'admin-user'
            'aws_region': 'us-east-1'
        },
        'biops-job-api': {
            'httpMethod': 'GET',
            'path': '/jobs'
        },
        'biops-orchestrator': {
            'config': {
                'source_account_id': '123456789012',
                'source_role_name': 'QuickSightRole',
                'source_asset_id': 'dashboard-id-123',
                'target_account_id': '210987654321',
                'target_role_name': 'QuickSightRole',
                'target_admin_user': 'admin-user',
                'bucket_name': 'biops-version-control-demo-2025',
                'dashboard_name': 'BIOpsDemo',
                'aws_region': 'us-east-1'
            }
        }
    }

if __name__ == "__main__":
    print("BIOPS Lambda Function Examples")
    print("Available functions:")
    
    payloads = example_payloads()
    for i, func_name in enumerate(payloads.keys(), 1):
        print(f"{i}. {func_name}")
    
    print("\nExample usage:")
    print("deploy_individual_steps('biops-export-assets', payload)")
    print("\nRunning export example:")
    
    # Example: Export assets
    #export_result = deploy_individual_steps('biops-export-assets', payloads['biops-export-assets'])
    
    # Extract values from export result
    """ 
    if export_result and export_result.get('statusCode') == 200:
        body = json.loads(export_result['body'])
        download_url = body.get('download_url')
        job_id = body.get('job_id')
        export_format = body.get('export_format')
        
        print(f"\nExtracted values:")
        print(f"Job ID: {job_id}")
        print(f"Export Format: {export_format}")
        print(f"Download URL: {download_url[:100]}...")
        
        # Update upload payload with extracted values
        upload_payload = payloads['biops-upload-assets'].copy()
        upload_payload['download_url'] = download_url
        upload_payload['job_id'] = job_id
        upload_payload['export_format'] = export_format
        upload_payload['bucket_name'] = 'biops-version-control-demo-038198578763'
        
        print(f"\nRunning upload with extracted values:")
        deploy_individual_steps('biops-upload-assets', upload_payload)
"""
    # Or, use orchestrator for complete workflow
    deploy_assets_example()

    # Example: Import assets
    # import_result = deploy_individual_steps('biops-import-assets', payloads['biops-import-assets'])

    # Example: Update permissions
    # permissions_result = deploy_individual_steps('biops-update-permissions', payloads['biops-update-permissions'])
    
    
    
    