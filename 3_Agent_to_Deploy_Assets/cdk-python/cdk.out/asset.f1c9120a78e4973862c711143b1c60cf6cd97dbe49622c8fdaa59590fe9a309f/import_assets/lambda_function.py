import json
import boto3
import time
from datetime import datetime
from shared.utils import assume_role

def lambda_handler(event, context):
    """Import QuickSight assets from S3 bundle."""
    try:
        # Handle API Gateway vs direct invocation
        if 'httpMethod' in event:
            http_method = event['httpMethod']
            path = event['path']
            
            if http_method == 'POST' and path == '/import':
                # Start import job
                body = json.loads(event['body'])
                s3_uri = body['s3_uri']
                source_asset_id = body['source_asset_id']
                target_account_id = body['target_account_id']
                target_role_name = body['target_role_name']
                aws_region = body.get('aws_region', 'us-east-1')
            
            elif http_method == 'GET' and '/import/' in path:
                # Get import job status
                import_job_id = path.split('/import/')[-1]
                body = json.loads(event.get('body', '{}'))
                target_account_id = body['target_account_id']
                target_role_name = body['target_role_name']
                aws_region = body.get('aws_region', 'us-east-1')
                
                # Assume role and get job status
                target_session = assume_role(target_account_id, target_role_name, aws_region)
                qs_client = target_session.client('quicksight')
                
                response = qs_client.describe_asset_bundle_import_job(
                    AwsAccountId=target_account_id,
                    AssetBundleImportJobId=import_job_id
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
            s3_uri = event['s3_uri']
            source_asset_id = event['source_asset_id']
            target_account_id = event['target_account_id']
            target_role_name = event['target_role_name']
            aws_region = event.get('aws_region', 'us-east-1')
        
        # Assume role in target account
        target_session = assume_role(target_account_id, target_role_name, aws_region)
        qs_client = target_session.client('quicksight')
        
        # Generate import job ID
        current_time = datetime.now().date()
        import_job_id = f"{source_asset_id}_{target_account_id}_{current_time}"
        
        # Start import job
        response = qs_client.start_asset_bundle_import_job(
            AwsAccountId=target_account_id,
            AssetBundleImportJobId=import_job_id,
            AssetBundleImportSource={
                'S3Uri': s3_uri
            },
            FailureAction='ROLLBACK'
        )
        
        # Wait for completion
        while True:
            status_response = qs_client.describe_asset_bundle_import_job(
                AwsAccountId=target_account_id,
                AssetBundleImportJobId=import_job_id
            )
            
            job_status = status_response['JobStatus']
            if job_status in ['SUCCESSFUL', 'FAILED', 'FAILED_ROLLBACK_COMPLETED']:
                break
            time.sleep(10)
        
        if job_status != 'SUCCESSFUL':
            error_details = {
                'error': f'Import job failed with status: {job_status}',
                'job_id': import_job_id,
                'status': job_status
            }
            
            # Add error details from QuickSight response
            if 'Errors' in status_response:
                error_details['errors'] = status_response['Errors']
            if 'RollbackErrors' in status_response:
                error_details['rollback_errors'] = status_response['RollbackErrors']
            if 'RequestId' in status_response:
                error_details['request_id'] = status_response['RequestId']
            
            return {
                'statusCode': 500,
                'body': json.dumps(error_details)
            }
        
        result = {
            'job_id': import_job_id,
            'status': job_status,
            'message': 'Assets imported successfully'
        }
        
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