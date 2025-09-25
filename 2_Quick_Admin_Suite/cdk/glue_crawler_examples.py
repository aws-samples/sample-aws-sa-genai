import boto3
import json

# Initialize Glue client
glue_client = boto3.client('glue')

def create_glue_crawler():
    """Create a Glue Crawler to catalog S3 data"""
    
    crawler_config = {
        'Name': 'admin-console-data-crawler',
        'Role': 'arn:aws:iam::123456789012:role/QuickSightAdminConsole2025',
        'DatabaseName': 'admin_console_db',
        'Targets': {
            'S3Targets': [
                {
                    'Path': 's3://admin-console-new-123456789012/monitoring/quicksight/',
                    'Exclusions': ['**/_SUCCESS', '**/.*']
                }
            ]
        },
        'SchemaChangePolicy': {
            'UpdateBehavior': 'UPDATE_IN_DATABASE',
            'DeleteBehavior': 'LOG'
        },
        'Configuration': json.dumps({
            'Version': 1.0,
            'CrawlerOutput': {
                'Partitions': {'AddOrUpdateBehavior': 'InheritFromTable'}
            }
        })
    }
    
    response = glue_client.create_crawler(**crawler_config)
    return response

def start_crawler():
    """Start the Glue Crawler"""
    response = glue_client.start_crawler(Name='admin-console-data-crawler')
    return response

def get_crawler_status():
    """Check crawler status"""
    response = glue_client.get_crawler(Name='admin-console-data-crawler')
    return response['Crawler']['State']

if __name__ == "__main__":
    # Create crawler
    create_response = create_glue_crawler()
    print(f"Crawler created: {create_response}")
    
    # Start crawler
    start_response = start_crawler()
    print(f"Crawler started: {start_response}")