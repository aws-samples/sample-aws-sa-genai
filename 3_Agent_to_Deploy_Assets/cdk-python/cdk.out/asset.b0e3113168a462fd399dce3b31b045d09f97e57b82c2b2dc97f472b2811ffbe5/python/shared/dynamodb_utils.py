import boto3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class JobStatusManager:
    def __init__(self, table_name: str = 'biops-job-runs'):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def create_job(self, job_id: str, payload: Dict, initiated_by: str) -> Dict:
        """Create new job record."""
        item = {
            'jobId': job_id,
            'status': 'PENDING',
            'createdAt': datetime.utcnow().isoformat() + 'Z',
            'updatedAt': datetime.utcnow().isoformat() + 'Z',
            'initiatedBy': initiated_by,
            'payload': payload,
            'currentStep': '',
            'steps': [],
            'retryCount': 0
        }
        
        self.table.put_item(Item=item)
        return item
    
    def update_job_status(self, job_id: str, status: str, current_step: str = None) -> None:
        """Update job status and current step."""
        update_expr = 'SET #status = :status, updatedAt = :updated'
        expr_values = {
            ':status': status,
            ':updated': datetime.utcnow().isoformat() + 'Z'
        }
        expr_names = {'#status': 'status'}
        
        if current_step:
            update_expr += ', currentStep = :step'
            expr_values[':step'] = current_step
        
        self.table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names
        )
    
    def add_step_result(self, job_id: str, step_name: str, status: str, 
                       output_s3_key: str = None, error_message: str = None) -> None:
        """Add or update step result."""
        step = {
            'name': step_name,
            'status': status,
            'endedAt': datetime.utcnow().isoformat() + 'Z'
        }
        
        if output_s3_key:
            step['outputS3Key'] = output_s3_key
        if error_message:
            step['errorMessage'] = error_message
        
        # Get current steps and update
        response = self.table.get_item(Key={'jobId': job_id})
        item = response.get('Item', {})
        steps = item.get('steps', [])
        
        # Find existing step or add new one
        step_found = False
        for i, existing_step in enumerate(steps):
            if existing_step['name'] == step_name:
                steps[i].update(step)
                step_found = True
                break
        
        if not step_found:
            step['startedAt'] = step['endedAt']
            steps.append(step)
        
        self.table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET steps = :steps, updatedAt = :updated',
            ExpressionAttributeValues={
                ':steps': steps,
                ':updated': datetime.utcnow().isoformat() + 'Z'
            }
        )
    
    def set_job_results(self, job_id: str, results: Dict) -> None:
        """Set final job results."""
        self.table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET results = :results, updatedAt = :updated',
            ExpressionAttributeValues={
                ':results': results,
                ':updated': datetime.utcnow().isoformat() + 'Z'
            }
        )
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID."""
        response = self.table.get_item(Key={'jobId': job_id})
        return response.get('Item')
    
    def list_jobs(self, limit: int = 50) -> List[Dict]:
        """List recent jobs."""
        response = self.table.scan(Limit=limit)
        return response.get('Items', [])