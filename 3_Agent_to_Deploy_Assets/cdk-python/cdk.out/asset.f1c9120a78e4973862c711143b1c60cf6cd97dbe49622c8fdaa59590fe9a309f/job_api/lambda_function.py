import json
import boto3
from shared.dynamodb_utils import JobStatusManager

def lambda_handler(event, context):
    """API Gateway handler for job management endpoints."""
    try:
        job_manager = JobStatusManager()
        http_method = event['httpMethod']
        path = event['path']
        
        if http_method == 'GET' and path == '/jobs':
            # List jobs
            jobs = job_manager.list_jobs()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'jobs': jobs})
            }
        
        elif http_method == 'GET' and '/jobs/' in path:
            # Get specific job
            job_id = path.split('/jobs/')[-1]
            job = job_manager.get_job(job_id)
            
            if not job:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Job not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(job)
            }
        
        elif http_method == 'POST' and path == '/jobs':
            # Start new job
            body = json.loads(event['body'])
            config = body['config']
            initiated_by = body.get('initiated_by', 'api-user')
            
            # Invoke orchestrator
            lambda_client = boto3.client('lambda')
            response = lambda_client.invoke(
                FunctionName='biops-orchestrator',
                InvocationType='Event',  # Async
                Payload=json.dumps({
                    'config': config,
                    'initiated_by': initiated_by
                })
            )
            
            return {
                'statusCode': 202,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Job started', 'status': 'PENDING'})
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }