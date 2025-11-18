import json
import boto3
from shared.utils import assume_role, get_user_arn

def lambda_handler(event, context):
    """Update permissions for imported QuickSight assets."""
    try:
        # Handle API Gateway vs direct invocation
        if 'httpMethod' in event and event['httpMethod'] == 'POST':
            body = json.loads(event['body'])
            dashboard_name = body['dashboard_name']
            target_account_id = body['target_account_id']
            target_role_name = body['target_role_name']
            target_admin_user = body['target_admin_user']
            aws_region = body.get('aws_region', 'us-east-1')
        else:
            # Direct Lambda invocation
            dashboard_name = event['dashboard_name']
            target_account_id = event['target_account_id']
            target_role_name = event['target_role_name']
            target_admin_user = event['target_admin_user']
            aws_region = event.get('aws_region', 'us-east-1')
        
        # Assume role in target account
        target_session = assume_role(target_account_id, target_role_name, aws_region)
        qs_client = target_session.client('quicksight')
        
        # Get admin user ARN
        target_admin_arn = get_user_arn(target_session, target_admin_user, aws_region)
        
        # Search for dashboard
        response = qs_client.search_dashboards(
            AwsAccountId=target_account_id,
            Filters=[
                {
                    'Operator': 'StringLike',
                    'Name': 'DASHBOARD_NAME',
                    'Value': dashboard_name
                },
            ]
        )
        
        if not response['DashboardSummaryList']:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Dashboard {dashboard_name} not found'})
            }
        
        dashboard_id = response['DashboardSummaryList'][0]['DashboardId']
        
        # Update dashboard permissions
        qs_client.update_dashboard_permissions(
            AwsAccountId=target_account_id,
            DashboardId=dashboard_id,
            GrantPermissions=[
                {
                    'Principal': target_admin_arn,
                    'Actions': [
                        "quicksight:DescribeDashboard",
                        "quicksight:ListDashboardVersions",
                        "quicksight:UpdateDashboardPermissions",
                        "quicksight:QueryDashboard",
                        "quicksight:UpdateDashboard",
                        "quicksight:DeleteDashboard",
                        "quicksight:DescribeDashboardPermissions",
                        "quicksight:UpdateDashboardPublishedVersion"
                    ]
                }
            ]
        )
        
        # Get dashboard details and update dataset permissions
        dashboard_response = qs_client.describe_dashboard(
            AwsAccountId=target_account_id,
            DashboardId=dashboard_id
        )
        
        datasets = dashboard_response['Dashboard']['Version']['DataSetArns']
        for dataset in datasets:
            dataset_id = dataset.split(":")[-1].split("/")[-1]
            qs_client.update_data_set_permissions(
                AwsAccountId=target_account_id,
                DataSetId=dataset_id,
                GrantPermissions=[
                    {
                        'Principal': target_admin_arn,
                        'Actions': [
                            "quicksight:UpdateDataSetPermissions",
                            "quicksight:DescribeDataSet",
                            "quicksight:DescribeDataSetPermissions",
                            "quicksight:PassDataSet",
                            "quicksight:DescribeIngestion",
                            "quicksight:ListIngestions",
                            "quicksight:UpdateDataSet",
                            "quicksight:DeleteDataSet",
                            "quicksight:CreateIngestion",
                            "quicksight:CancelIngestion"
                        ]
                    }
                ]
            )
        
        result = {
            'dashboard_id': dashboard_id,
            'datasets_updated': len(datasets),
            'message': 'Permissions updated successfully'
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