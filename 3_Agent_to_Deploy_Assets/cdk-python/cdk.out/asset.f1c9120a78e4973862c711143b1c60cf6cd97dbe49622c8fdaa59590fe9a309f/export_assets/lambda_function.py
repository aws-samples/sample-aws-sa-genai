import json
import boto3
import time
from datetime import datetime
import sys
import os

sys.path.append('/opt/python')
from shared.utils import assume_role, default_botocore_config

def lambda_handler(event, context):
    """Export QuickSight assets as bundle."""
    try:
        # Handle API Gateway vs direct invocation
        if 'httpMethod' in event:
            # API Gateway request
            http_method = event['httpMethod']
            path = event['path']
            
            if http_method == 'POST' and path == '/export':
                # Start export job
                body = json.loads(event['body'])
                source_account_id = body['source_account_id']
                source_role_name = body['source_role_name']
                source_asset_id = body['source_asset_id']
                aws_region = body.get('aws_region', 'us-east-1')
            
            elif http_method == 'GET' and '/export/' in path:
                # Get export job status
                export_job_id = path.split('/export/')[-1]
                body = json.loads(event.get('body', '{}'))
                source_account_id = body['source_account_id']
                source_role_name = body['source_role_name']
                aws_region = body.get('aws_region', 'us-east-1')
                
                # Assume role and get job status
                source_session = assume_role(source_account_id, source_role_name, aws_region)
                qs_client = source_session.client('quicksight')
                
                response = qs_client.describe_asset_bundle_export_job(
                    AwsAccountId=source_account_id,
                    AssetBundleExportJobId=export_job_id
                )
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(response)
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Endpoint not found'})
                }
        else:
            # Direct Lambda invocation
            source_account_id = event['source_account_id']
            source_role_name = event['source_role_name']
            source_asset_id = event['source_asset_id']
            aws_region = event.get('aws_region', 'us-east-1')
        
        # Assume role in source account
        source_session = assume_role(source_account_id, source_role_name, aws_region)
        qs_client = source_session.client('quicksight')
        
        # Generate job ID
        current_time = datetime.now().date()
        job_id = f"{source_asset_id}_{source_account_id}_{current_time}"
        
        # Start export job
        response = qs_client.start_asset_bundle_export_job(
            AwsAccountId=source_account_id,
            AssetBundleExportJobId=job_id,
            ResourceArns=[
                f"arn:aws:quicksight:{aws_region}:{source_account_id}:dashboard/{source_asset_id}",
            ],
            IncludeAllDependencies=True,
            IncludePermissions=False,
            ExportFormat='QUICKSIGHT_JSON'
        )
        
        # Wait for completion
        while True:
            status_response = qs_client.describe_asset_bundle_export_job(
                AwsAccountId=source_account_id,
                AssetBundleExportJobId=job_id
            )
            
            job_status = status_response['JobStatus']
            if job_status in ['SUCCESSFUL', 'FAILED']:
                break
            time.sleep(10)
        
        if job_status == 'FAILED':
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Export job failed',
                    'job_id': job_id
                })
            }
        
        result = {
            'job_id': job_id,
            'download_url': status_response['DownloadUrl'],
            'export_format': status_response['ExportFormat']
        }
        
        # Return appropriate format based on invocation type
        if 'httpMethod' in event:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        
    except Exception as e:
        error_response = {'error': str(e)}
        
        if 'httpMethod' in event:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(error_response)
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps(error_response)
            }