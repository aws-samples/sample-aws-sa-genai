import boto3

# Create QuickSight clients using wavicle profile
session = boto3.Session(profile_name='wavicle')
qs_client_east1 = session.client('quicksight', region_name='us-east-1')  # For user management
qs_client_east2 = session.client('quicksight', region_name='us-east-2')  # For data sources
account_id = session.client('sts').get_caller_identity()['Account']

def update_datasource_permissions(datasource_id, principal_arn, actions):
    """Update data source permissions for a given principal"""
    return qs_client_east2.update_data_source_permissions(
        AwsAccountId=account_id,
        DataSourceId=datasource_id,
        GrantPermissions=[
            {
                'Principal': principal_arn,
                'Actions': actions
            }
        ]
    )

# Get user ARN
users = qs_client_east1.list_users(AwsAccountId=account_id, Namespace='default')
for user in users['UserList']:
    if 'wangzyn@amazon.com' in user['UserName']:
        principal_arn = user['Arn']
        break

# List all data sources
datasources = qs_client_east2.list_data_sources(AwsAccountId=account_id)

# Data source actions
datasource_actions = [
    "quicksight:DescribeDataSource",
    "quicksight:DescribeDataSourcePermissions",
    "quicksight:PassDataSource",
    "quicksight:UpdateDataSource",
    "quicksight:DeleteDataSource",
    "quicksight:UpdateDataSourcePermissions"
]

print(f"Found {len(datasources['DataSources'])} data sources:")

# Grant permissions for each data source
for datasource in datasources['DataSources']:
    datasource_id = datasource['DataSourceId']
    datasource_name = datasource['Name']
    print(f"- {datasource_name} ({datasource_id})")
    
    response = update_datasource_permissions(datasource_id, principal_arn, datasource_actions)
    print(f"  Permissions updated: {response['Status']}")