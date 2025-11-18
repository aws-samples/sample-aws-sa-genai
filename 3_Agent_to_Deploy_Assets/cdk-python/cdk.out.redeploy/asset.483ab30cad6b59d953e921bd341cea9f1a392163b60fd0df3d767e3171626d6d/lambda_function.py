import json
import boto3
import requests
import tempfile
import os
from shared.utils import assume_role

def lambda_handler(event, context):
    """Upload exported assets to S3 bucket."""
    try:
        # Handle API Gateway vs direct invocation
        if 'httpMethod' in event and event['httpMethod'] == 'POST':
            body = json.loads(event['body'])
            download_url = body['download_url']
            job_id = body['job_id']
            export_format = body['export_format']
            bucket_name = body['bucket_name']
            target_account_id = body['target_account_id']
            target_role_name = body['target_role_name']
            aws_region = body.get('aws_region', 'us-east-1')
        else:
            # Direct Lambda invocation
            download_url = event['download_url']
            job_id = event['job_id']
            export_format = event['export_format']
            bucket_name = event['bucket_name']
            target_account_id = event['target_account_id']
            target_role_name = event['target_role_name']
            aws_region = event.get('aws_region', 'us-east-1')
        
        # Assume role in target account
        target_session = assume_role(target_account_id, target_role_name, aws_region)
        s3_client = target_session.client('s3')
        
        # Download file from URL
        response = requests.get(download_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download file. Status code: {response.status_code}")
        
        # Prepare S3 key
        local_path = f"{export_format}_{job_id}"
        local_file_name = f"{local_path}.zip"
        s3_key = f"{local_path}/{local_file_name}"
        
        # Upload to S3
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(response.content)
            temp_file.flush()
            s3_client.upload_file(temp_file.name, bucket_name, s3_key)
        
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        
        result = {
            'bucket_name': bucket_name,
            's3_key': s3_key,
            's3_uri': s3_uri,
            'job_id': job_id
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