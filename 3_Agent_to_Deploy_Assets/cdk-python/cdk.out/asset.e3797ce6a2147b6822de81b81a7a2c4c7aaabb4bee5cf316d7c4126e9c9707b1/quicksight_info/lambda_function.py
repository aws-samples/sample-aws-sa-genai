import json
import boto3
from shared.utils import assume_role

def lambda_handler(event, context):
    """QuickSight information retrieval API."""
    try:
        # Handle API Gateway request
        if 'httpMethod' in event:
            http_method = event['httpMethod']
            path = event['path']
            body = json.loads(event.get('body', '{}'))
        else:
            # Direct invocation
            http_method = event.get('method', 'GET')
            path = event.get('path', '')
            body = event
        
        # Extract common parameters
        account_id = body.get('account_id')
        role_name = body.get('role_name')
        aws_region = body.get('aws_region', 'us-east-1')
        
        if not account_id or not role_name:
            return error_response('account_id and role_name are required')
        
        # Assume role and create QuickSight client
        session = assume_role(account_id, role_name, aws_region)
        qs_client = session.client('quicksight')
        
        # Route to appropriate handler
        if '/dashboards' in path and http_method == 'GET':
            return list_dashboards(qs_client, account_id)
        elif '/dashboard/' in path and '/definition' in path:
            dashboard_id = extract_id_from_path(path, 'dashboard')
            return describe_dashboard_definition(qs_client, account_id, dashboard_id)
        elif '/dashboard/' in path and '/datasets' in path:
            dashboard_id = extract_id_from_path(path, 'dashboard')
            return get_dashboard_datasets(qs_client, account_id, dashboard_id)
        elif '/dashboard/' in path and '/permissions' in path:
            dashboard_id = extract_id_from_path(path, 'dashboard')
            return describe_dashboard_permissions(qs_client, account_id, dashboard_id)
        elif '/dataset/' in path and '/definition' in path:
            dataset_id = extract_id_from_path(path, 'dataset')
            return get_dataset_definition(qs_client, account_id, dataset_id)
        elif '/dataset/' in path and '/datasources' in path:
            dataset_id = extract_id_from_path(path, 'dataset')
            return get_dataset_datasources(qs_client, account_id, dataset_id)
        elif '/dataset/' in path and '/permissions' in path:
            dataset_id = extract_id_from_path(path, 'dataset')
            return describe_dataset_permissions(qs_client, account_id, dataset_id)
        elif '/users' in path and http_method == 'GET':
            return list_users(qs_client, account_id)
        else:
            return error_response('Endpoint not found', 404)
            
    except Exception as e:
        return error_response(str(e), 500)

def list_dashboards(qs_client, account_id):
    """List all dashboards."""
    response = qs_client.list_dashboards(AwsAccountId=account_id)
    return success_response(response['DashboardSummaryList'])

def describe_dashboard_definition(qs_client, account_id, dashboard_id):
    """Get dashboard definition."""
    response = qs_client.describe_dashboard_definition(
        AwsAccountId=account_id,
        DashboardId=dashboard_id
    )
    return success_response(response['Definition'])

def get_dashboard_datasets(qs_client, account_id, dashboard_id):
    """Get datasets used by a dashboard."""
    response = qs_client.describe_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboard_id
    )
    datasets = response['Dashboard']['Version']['DataSetArns']
    dataset_list = [arn.split('/')[-1] for arn in datasets]
    return success_response({'datasets': dataset_list})

def describe_dashboard_permissions(qs_client, account_id, dashboard_id):
    """Get dashboard permissions."""
    response = qs_client.describe_dashboard_permissions(
        AwsAccountId=account_id,
        DashboardId=dashboard_id
    )
    return success_response(response['Permissions'])

def get_dataset_definition(qs_client, account_id, dataset_id):
    """Get dataset definition."""
    response = qs_client.describe_data_set(
        AwsAccountId=account_id,
        DataSetId=dataset_id
    )
    return success_response(response['DataSet'])

def get_dataset_datasources(qs_client, account_id, dataset_id):
    """Get data sources for a dataset."""
    response = qs_client.describe_data_set(
        AwsAccountId=account_id,
        DataSetId=dataset_id
    )
    datasources = []
    for source in response['DataSet'].get('PhysicalTableMap', {}).values():
        if 'RelationalTable' in source:
            datasources.append({
                'type': 'RelationalTable',
                'data_source_arn': source['RelationalTable']['DataSourceArn']
            })
        elif 'CustomSql' in source:
            datasources.append({
                'type': 'CustomSql',
                'data_source_arn': source['CustomSql']['DataSourceArn']
            })
    return success_response({'datasources': datasources})

def describe_dataset_permissions(qs_client, account_id, dataset_id):
    """Get dataset permissions."""
    response = qs_client.describe_data_set_permissions(
        AwsAccountId=account_id,
        DataSetId=dataset_id
    )
    return success_response(response['Permissions'])

def list_users(qs_client, account_id):
    """List QuickSight users."""
    response = qs_client.list_users(
        AwsAccountId=account_id,
        Namespace='default'
    )
    return success_response(response['UserList'])

def extract_id_from_path(path, resource_type):
    """Extract resource ID from path."""
    parts = path.split('/')
    try:
        idx = parts.index(resource_type) + 1
        return parts[idx]
    except (ValueError, IndexError):
        raise ValueError(f"Invalid path format for {resource_type}")

def success_response(data):
    """Return success response."""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(data)
    }

def error_response(message, status_code=400):
    """Return error response."""
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }