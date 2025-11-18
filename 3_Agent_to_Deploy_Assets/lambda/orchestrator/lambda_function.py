import json
import boto3
import uuid
from datetime import datetime
import sys
import os

sys.path.append('/opt/python')
from shared.dynamodb_utils import JobStatusManager

def lambda_handler(event, context):
    """Orchestrate the complete asset deployment workflow."""
    try:
        lambda_client = boto3.client('lambda')
        job_manager = JobStatusManager()
        
        # Generate job ID and create job record
        job_id = f"job-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
        initiated_by = event.get('initiated_by', 'system')
        
        # Parse configuration
        config = event['config']
        
        # Create job record
        job_manager.create_job(job_id, config, initiated_by)
        job_manager.update_job_status(job_id, 'RUNNING', 'biops-export-assets')
        source_account_id = config['source_account_id']
        source_role_name = config['source_role_name']
        source_asset_id = config['source_asset_id']
        target_account_id = config['target_account_id']
        target_role_name = config['target_role_name']
        target_admin_user = config['target_admin_user']
        bucket_name = config['bucket_name']
        dashboard_name = config.get('dashboard_name', 'BIOpsDemo')
        aws_region = config.get('aws_region', 'us-east-1')
        
        # Step 1: Export assets
        export_payload = {
            'source_account_id': source_account_id,
            'source_role_name': source_role_name,
            'source_asset_id': source_asset_id,
            'aws_region': aws_region
        }
        
        export_response = lambda_client.invoke(
            FunctionName='biops-export-assets',
            InvocationType='RequestResponse',
            Payload=json.dumps(export_payload)
        )
        
        export_result = json.loads(export_response['Payload'].read())
        if export_result['statusCode'] != 200:
            job_manager.add_step_result(job_id, 'biops-export-assets', 'FAILED', 
                                      error_message=export_result.get('body', 'Export failed'))
            job_manager.update_job_status(job_id, 'FAILED')
            return export_result
        
        export_data = json.loads(export_result['body'])
        job_manager.add_step_result(job_id, 'biops-export-assets', 'SUCCEEDED', 
                                  output_s3_key=export_data.get('download_url'))
        job_manager.update_job_status(job_id, 'RUNNING', 'biops-upload-assets')
        
        # Step 2: Upload to S3
        upload_payload = {
            'download_url': export_data['download_url'],
            'job_id': export_data['job_id'],
            'export_format': export_data['export_format'],
            'bucket_name': bucket_name,
            'target_account_id': target_account_id,
            'target_role_name': target_role_name,
            'aws_region': aws_region
        }
        
        upload_response = lambda_client.invoke(
            FunctionName='biops-upload-assets',
            InvocationType='RequestResponse',
            Payload=json.dumps(upload_payload)
        )
        
        upload_result = json.loads(upload_response['Payload'].read())
        if upload_result['statusCode'] != 200:
            job_manager.add_step_result(job_id, 'biops-upload-assets', 'FAILED',
                                      error_message=upload_result.get('body', 'Upload failed'))
            job_manager.update_job_status(job_id, 'FAILED')
            return upload_result
        
        upload_data = json.loads(upload_result['body'])
        job_manager.add_step_result(job_id, 'biops-upload-assets', 'SUCCEEDED',
                                  output_s3_key=upload_data.get('s3_uri'))
        job_manager.update_job_status(job_id, 'RUNNING', 'biops-import-assets')
        
        # Step 3: Import assets
        import_payload = {
            's3_uri': upload_data['s3_uri'],
            'source_asset_id': source_asset_id,
            'target_account_id': target_account_id,
            'target_role_name': target_role_name,
            'aws_region': aws_region
        }
        
        import_response = lambda_client.invoke(
            FunctionName='biops-import-assets',
            InvocationType='RequestResponse',
            Payload=json.dumps(import_payload)
        )
        
        import_result = json.loads(import_response['Payload'].read())
        if import_result['statusCode'] != 200:
            job_manager.add_step_result(job_id, 'biops-import-assets', 'FAILED',
                                      error_message=import_result.get('body', 'Import failed'))
            job_manager.update_job_status(job_id, 'FAILED')
            return import_result
        
        job_manager.add_step_result(job_id, 'biops-import-assets', 'SUCCEEDED')
        job_manager.update_job_status(job_id, 'RUNNING', 'biops-update-permissions')
        
        # Step 4: Update permissions
        permissions_payload = {
            'dashboard_name': dashboard_name,
            'target_account_id': target_account_id,
            'target_role_name': target_role_name,
            'target_admin_user': target_admin_user,
            'aws_region': aws_region
        }
        
        permissions_response = lambda_client.invoke(
            FunctionName='biops-update-permissions',
            InvocationType='RequestResponse',
            Payload=json.dumps(permissions_payload)
        )
        
        permissions_result = json.loads(permissions_response['Payload'].read())
        
        if permissions_result['statusCode'] == 200:
            job_manager.add_step_result(job_id, 'biops-update-permissions', 'SUCCEEDED')
            job_manager.update_job_status(job_id, 'COMPLETED')
            
            # Set final results
            results = {
                'export_job_id': export_data['job_id'],
                'import_job_id': json.loads(import_result['body'])['job_id'],
                's3_uri': upload_data['s3_uri'],
                'dashboard_id': json.loads(permissions_result['body']).get('dashboard_id')
            }
            job_manager.set_job_results(job_id, results)
        else:
            job_manager.add_step_result(job_id, 'biops-update-permissions', 'FAILED',
                                      error_message=permissions_result.get('body', 'Permissions update failed'))
            job_manager.update_job_status(job_id, 'FAILED')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'job_id': job_id,
                'message': 'Asset deployment completed successfully',
                'export_job_id': export_data['job_id'],
                'import_job_id': json.loads(import_result['body'])['job_id'],
                's3_uri': upload_data['s3_uri'],
                'permissions_status': permissions_result['statusCode']
            })
        }
        
    except Exception as e:
        # Update job status to failed if job_id exists
        try:
            if 'job_id' in locals():
                job_manager.update_job_status(job_id, 'FAILED')
        except:
            pass
            
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'job_id': locals().get('job_id', 'unknown')
            })
        }