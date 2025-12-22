import boto3

# Create QuickSight clients using wavicle profile
session = boto3.Session(profile_name='wavicle')
qs_client_east1 = session.client('quicksight', region_name='us-east-1')  # For user management
qs_client_east2 = session.client('quicksight', region_name='us-east-2')  # For analysis/datasets
account_id = session.client('sts').get_caller_identity()['Account']

def update_analysis_permissions(analysis_id, principal_arn, actions):
    """Update analysis permissions for a given principal"""
    return qs_client_east2.update_analysis_permissions(
        AwsAccountId=account_id,
        AnalysisId=analysis_id,
        GrantPermissions=[
            {
                'Principal': principal_arn,
                'Actions': actions
            }
        ]
    )

def update_dataset_permissions(dataset_id, principal_arn, actions):
    """Update dataset permissions for a given principal"""
    return qs_client_east2.update_data_set_permissions(
        AwsAccountId=account_id,
        DataSetId=dataset_id,
        GrantPermissions=[
            {
                'Principal': principal_arn,
                'Actions': actions
            }
        ]
    )

# Example usage - list dashboards
#response = qs_client.list_dashboards(AwsAccountId=account_id)

# All analysis actions
actions = [
    "quicksight:RestoreAnalysis",
    "quicksight:UpdateAnalysisPermissions",
    "quicksight:DeleteAnalysis",
    "quicksight:DescribeAnalysisPermissions",
    "quicksight:QueryAnalysis",
    "quicksight:DescribeAnalysis",
    "quicksight:UpdateAnalysis"
]

# List QuickSight users to get correct principal ARN
users = qs_client_east1.list_users(AwsAccountId=account_id, Namespace='default')
for user in users['UserList']:
    if 'wangzyn@amazon.com' in user['UserName']:
        print(f"Correct ARN: {user['Arn']}")
        principal_arn = user['Arn']
        break

analysis_id = 'e8ee2735-96e5-40f4-88b8-51d77008197a'

# Update analysis permissions
response = update_analysis_permissions(analysis_id, principal_arn, actions)
print("Analysis permissions updated:", response)

# Get analysis details to find datasets
analysis = qs_client_east2.describe_analysis(AwsAccountId=account_id, AnalysisId=analysis_id)
dataset_arns = analysis['Analysis']['DataSetArns']

# Dataset actions
dataset_actions = [
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

# Update permissions for each dataset
for dataset_arn in dataset_arns:
    dataset_id = dataset_arn.split('/')[-1]
    dataset_response = update_dataset_permissions(dataset_id, principal_arn, dataset_actions)
    print(f"Dataset {dataset_id} permissions updated:", dataset_response)