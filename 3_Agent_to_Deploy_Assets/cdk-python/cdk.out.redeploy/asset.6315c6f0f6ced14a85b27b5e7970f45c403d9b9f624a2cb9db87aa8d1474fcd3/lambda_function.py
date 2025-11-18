import json
import boto3
import tempfile
import urllib.request

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
            aws_region = body.get('aws_region', 'us-east-1')
        else:
            # Direct Lambda invocation
            download_url = event['download_url']
            job_id = event['job_id']
            export_format = event['export_format']
            bucket_name = event['bucket_name']
            aws_region = event.get('aws_region', 'us-east-1')
        
        # Use tools account S3 client (no role assumption needed)
        s3_client = boto3.client('s3', region_name=aws_region)
        
        # Download file from URL using urllib
        with urllib.request.urlopen(download_url) as response:
            file_data = response.read()
        
        # Prepare S3 key
        local_path = f"{export_format}_{job_id}"
        local_file_name = f"{local_path}.qs"
        s3_key = f"{local_path}/{local_file_name}"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_data
        )
        
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