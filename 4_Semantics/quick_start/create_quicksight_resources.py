import boto3
import json
import os

# Load AWS profile
AWS_PROFILE = os.getenv('AWS_PROFILE', 'quick_suite_sa')
session = boto3.Session(profile_name=AWS_PROFILE)

# Initialize clients
quicksight = session.client('quicksight', region_name='us-east-1')
sts = session.client('sts')
account_id = sts.get_caller_identity()['Account']

print(f"Using AWS Account ID: {account_id}")

# Delete existing data source if it exists
datasource_id = 'movies-snowflake-datasource'
try:
    quicksight.delete_data_source(
        AwsAccountId=account_id,
        DataSourceId=datasource_id
    )
    print(f"Existing data source deleted: {datasource_id}")
except quicksight.exceptions.ResourceNotFoundException:
    print(f"No existing data source found: {datasource_id}")

# Snowflake configuration (from secrets)
SNOWFLAKE_CONFIG = {
    'account': 'awspartner',
    'database': 'MOVIES',
    'warehouse': 'WORKSHOPWH',
    'user': 'QUICKSA',
    'password': 'Jungfrau.9282!'
}

# Create Snowflake Data Source
datasource_id = 'movies-snowflake-datasource'
datasource_response = quicksight.create_data_source(
    AwsAccountId=account_id,
    DataSourceId=datasource_id,
    Name='Movies Snowflake Data Source',
    Type='SNOWFLAKE',
    DataSourceParameters={
        'SnowflakeParameters': {
            'Host': f"{SNOWFLAKE_CONFIG['account']}.snowflakecomputing.com",
            'Database': SNOWFLAKE_CONFIG['database'],
            'Warehouse': SNOWFLAKE_CONFIG['warehouse']
        }
    },
    Credentials={
        'CredentialPair': {
            'Username': SNOWFLAKE_CONFIG['user'],
            'Password': SNOWFLAKE_CONFIG['password']
        }
    }
)

print(f"Data Source Created: {datasource_response['DataSourceId']}")

# Delete existing dataset if it exists
import time
dataset_id = 'movies-dashboard-dataset'
try:
    quicksight.delete_data_set(
        AwsAccountId=account_id,
        DataSetId=dataset_id
    )
    print(f"Existing dataset deleted: {dataset_id}, waiting for deletion to complete...")
    time.sleep(10)  # Wait for deletion to complete
except quicksight.exceptions.ResourceNotFoundException:
    print(f"No existing dataset found: {dataset_id}")

# Create Dataset with base table
dataset_response = quicksight.create_data_set(
    AwsAccountId=account_id,
    DataSetId=dataset_id,
    Name='Movies Dashboard Dataset',
    PhysicalTableMap={
        'moviesdashboard': {
            'RelationalTable': {
                'DataSourceArn': f"arn:aws:quicksight:us-east-1:{account_id}:datasource/{datasource_id}",
                'Catalog': SNOWFLAKE_CONFIG['database'],
                'Schema': 'PUBLIC',
                'Name': 'MOVIES_DASHBOARD',
                'InputColumns': [
                    {'Name': 'GENRE', 'Type': 'STRING'},
                    {'Name': 'INTERACTION_TIMESTAMP', 'Type': 'INTEGER'},
                    {'Name': 'INTERACTION_TYPE', 'Type': 'STRING'},
                    {'Name': 'MOVIE_ID', 'Type': 'INTEGER'},
                    {'Name': 'MOVIE_RELEASE_YEAR', 'Type': 'INTEGER'},
                    {'Name': 'MOVIE_TITLE', 'Type': 'STRING'},
                    {'Name': 'USER_CITY', 'Type': 'STRING'},
                    {'Name': 'USER_COUNTRY', 'Type': 'STRING'},
                    {'Name': 'USER_EMAIL', 'Type': 'STRING'},
                    {'Name': 'USER_FIRSTNAME', 'Type': 'STRING'},
                    {'Name': 'USER_ID', 'Type': 'INTEGER'},
                    {'Name': 'USER_LASTNAME', 'Type': 'STRING'},
                    {'Name': 'USER_PHONENUMBER', 'Type': 'STRING'},
                    {'Name': 'USER_STATE', 'Type': 'STRING'},
                    {'Name': 'RATING_TIMESTAMP', 'Type': 'DATETIME'},
                    {'Name': 'USER_RATING', 'Type': 'DECIMAL'}
                ]
            }
        }
    },
    LogicalTableMap={
        'movieslogical': {
            'Alias': 'Movies Data',
            'Source': {
                'PhysicalTableId': 'moviesdashboard'
            },
            'DataTransforms': [
                {
                    'ProjectOperation': {
                        'ProjectedColumns': [
                            'GENRE',
                            'INTERACTION_TIMESTAMP',
                            'INTERACTION_TYPE',
                            'MOVIE_ID',
                            'MOVIE_RELEASE_YEAR',
                            'MOVIE_TITLE',
                            'USER_CITY',
                            'USER_COUNTRY',
                            'USER_EMAIL',
                            'USER_FIRSTNAME',
                            'USER_ID',
                            'USER_LASTNAME',
                            'USER_PHONENUMBER',
                            'USER_STATE',
                            'RATING_TIMESTAMP',
                            'USER_RATING'
                        ]
                    }
                }
            ]
        }
    },
    ImportMode='SPICE',
    FieldFolders={
        'Movie Information': {
            'description': 'Fields related to movie details',
            'columns': ['MOVIE_ID', 'MOVIE_TITLE', 'MOVIE_RELEASE_YEAR', 'GENRE']
        },
        'User Information': {
            'description': 'Fields related to user details',
            'columns': ['USER_ID', 'USER_FIRSTNAME', 'USER_LASTNAME', 'USER_EMAIL', 
                       'USER_PHONENUMBER', 'USER_CITY', 'USER_STATE', 'USER_COUNTRY']
        },
        'Interactions': {
            'description': 'Fields related to user interactions',
            'columns': ['INTERACTION_TYPE', 'INTERACTION_TIMESTAMP', 'RATING_TIMESTAMP', 'USER_RATING']
        }
    },
    DataSetUsageConfiguration={
        'DisableUseAsDirectQuerySource': True,
        'DisableUseAsImportedSource': False
    }
)

print(f"Dataset Created: {dataset_response['DataSetId']}")

# Create SPICE ingestion
import time
ingestion_id = f"ingestion-{int(time.time())}"
ingestion_response = quicksight.create_ingestion(
    AwsAccountId=account_id,
    DataSetId=dataset_id,
    IngestionId=ingestion_id,
    IngestionType='FULL_REFRESH'
)

print(f"SPICE Ingestion Started: {ingestion_response['IngestionId']}")
print(f"Ingestion Status: {ingestion_response['IngestionStatus']}")

# Share dataset with specific user
share_user = 'ElevatedAccess/wangzyn-Isengard' #os.getenv('QUICKSIGHT_USER', 'Admin/quicksight-sa')  # Format: namespace/username
permissions_response = quicksight.update_data_set_permissions(
    AwsAccountId=account_id,
    DataSetId=dataset_id,
    GrantPermissions=[
        {
            'Principal': f"arn:aws:quicksight:us-east-1:{account_id}:user/default/{share_user}",
            'Actions': [
                'quicksight:UpdateDataSetPermissions',
                'quicksight:DescribeDataSet',
                'quicksight:DescribeDataSetPermissions',
                'quicksight:PassDataSet',
                'quicksight:DescribeIngestion',
                'quicksight:ListIngestions',
                'quicksight:UpdateDataSet',
                'quicksight:DeleteDataSet',
                'quicksight:CreateIngestion',
                'quicksight:CancelIngestion'
            ]
        }
    ]
)

print(f"Dataset shared with user: {share_user}")

# Update field descriptions
field_descriptions = {
    'GENRE': 'The type of movie genre, such as action, comedy, drama, etc., that categorizes the movie\'s style, tone, and content.',
    'INTERACTION_TIMESTAMP': 'The timestamp when a user interacted with the movie, representing the number of seconds that have elapsed since January 1, 1970, at 00:00:00 UTC.',
    'INTERACTION_TYPE': 'The type of interaction a user had with a movie, either clicking on it or watching it.',
    'MOVIE_ID': 'Unique identifier for each movie in the database.',
    'MOVIE_RELEASE_YEAR': 'The year in which the movie was released.',
    'MOVIE_TITLE': 'The title of the movie.',
    'USER_CITY': 'The city where the user is located.',
    'USER_COUNTRY': 'The country where the user is located.',
    'USER_EMAIL': 'The email address of the user who interacted with the movie content.',
    'USER_FIRSTNAME': 'The first name of the user who interacted with the movie.',
    'USER_ID': 'Unique identifier for the user who interacted with the movie.',
    'USER_LASTNAME': 'The last name of the user who interacted with the movie.',
    'USER_PHONENUMBER': 'The phone number of the user who interacted with the movie content.',
    'USER_STATE': 'The state in which the user is located.',
    'RATING_TIMESTAMP': 'The date and time when a movie rating was recorded.',
    'USER_RATING': 'Average rating given by users to a movie, on a scale of 1 to 5.'
}

# Note: QuickSight API doesn't directly support setting field descriptions via create_data_set
# Field descriptions are typically set through the QuickSight UI or by using calculated fields
# This structure provides the foundation for the dataset

print("QuickSight Data Source and Dataset created successfully!")
print(f"Data Source ARN: arn:aws:quicksight:us-east-1:{account_id}:datasource/{datasource_id}")
print(f"Dataset ARN: arn:aws:quicksight:us-east-1:{account_id}:dataset/{dataset_id}")
print(f"Ingestion ARN: arn:aws:quicksight:us-east-1:{account_id}:dataset/{dataset_id}/ingestion/{ingestion_id}")
