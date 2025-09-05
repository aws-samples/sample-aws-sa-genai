import boto3
import csv
import io
import sys
import datetime
from awsglue.utils import getResolvedOptions
import logging
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

try:
    # Get job parameters
    args = getResolvedOptions(sys.argv, ['output_s3_path', 'region', 'aws_account_id'])
    output_s3_path = args['output_s3_path']
    region = args['region']
    account_id = args['aws_account_id']

    logger.info(f"Starting job with parameters: region={region}, account_id={account_id}, output_path={output_s3_path}")

    # Initialize QuickSight client
    qs_client = boto3.client('quicksight', region_name=region)
    
    def get_all_topics():
        """Retrieve all QuickSight topics."""
        topics = []
        next_token = None
        while True:
            params = {'AwsAccountId': account_id}
            if next_token:
                params['NextToken'] = next_token
            response = qs_client.list_topics(**params)
    #        print("list_topic_response:", response['TopicsSummaries'])
            topics.extend(response['TopicsSummaries'])
            next_token = response.get('NextToken')
            if not next_token:
                break
            print(topics)
        return topics

    def get_topic_permissions(topic_id):
        """Get permissions for a specific topic."""
        try:
            logger.info(f"Fetching permissions for topic: {topic_id}")
            response = qs_client.describe_topic_permissions(
                AwsAccountId=account_id,
                TopicId=topic_id
            )
            permissions = response.get('Permissions', [])
            logger.info(f"Retrieved {len(permissions)} permissions for topic {topic_id}")
            return permissions
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Error getting permissions for topic {topic_id}: {error_code} - {error_message}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting permissions for topic {topic_id}: {str(e)}")
            return []

    def build_csv_data():
        """Build CSV data from topics and permissions."""
        rows = []
        try:
            topics = get_all_topics()
            
            if not topics:
                logger.warning("No topics found in the account")
                return rows
                
            for topic in topics:
                topic_id = topic.get('TopicId')
                topic_name = topic.get('Name', '')
                logger.info(f"Processing topic: {topic_name} (ID: {topic_id})")
                
                permissions = get_topic_permissions(topic_id)
                
                if not permissions:
                    logger.warning(f"No permissions found for topic: {topic_name}")
                    continue
                
                for perm in permissions:
                    principal = perm.get('Principal', '')
                    actions = perm.get('Actions', [])
                    namespace = perm.get('PrincipalNamespace', '')
                    
                    name = principal.split('/')[-1] if '/' in principal else principal
                    principal_type = "Group" if ":group/" in principal else "User" if ":user/" in principal else "Unknown"
                    
                    rows.append({
                        'AWS Account ID': account_id,
                        'Region': region,
                        'Asset Type': 'Q Topic',
                        'Q Topic Name': topic_name,
                        'Q Topic ID': topic_id,
                        'Permission granted': principal_type,
                        'Owner Name': name,
                        'ARN': principal,
                        'Namespace': namespace,
                        'permissions set': '|'.join(actions)
                    })
            
            logger.info(f"Total rows generated: {len(rows)}")
            return rows
            
        except Exception as e:
            logger.error(f"Error building CSV data: {str(e)}")
            raise

    def write_to_s3(csv_data, fieldnames):
        """Write CSV data to S3."""
        try:
            if not csv_data:
                logger.warning("No data to write to CSV")
                return None

            # Create CSV in memory
            csv_buffer = io.StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            for row in csv_data:
                writer.writerow(row)

            # Parse S3 path
            bucket_name = output_s3_path.replace("s3://", "").split('/')[0]
            prefix = "/".join(output_s3_path.replace("s3://", "").split('/')[1:])
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{prefix}/q_object_access.csv"

            # Upload to S3
            s3 = boto3.client('s3')
            s3.put_object(
                Bucket=bucket_name,
                Key=filename,
                Body=csv_buffer.getvalue().encode('utf-8')
            )
            
            logger.info(f"Successfully wrote CSV to s3://{bucket_name}/{filename}")
            return f"s3://{bucket_name}/{filename}"
            
        except Exception as e:
            logger.error(f"Error writing to S3: {str(e)}")
            raise

    # Main execution
    fieldnames = [
        'AWS Account ID', 'Region', 'Asset Type',
        'Q Topic Name', 'Q Topic ID',
        'Permission granted', 'Owner Name',
        'ARN', 'Namespace',
        'permissions set'
    ]

    # Test QuickSight API access
    try:
        qs_client.list_topics(AwsAccountId=account_id)
        logger.info("Successfully verified QuickSight API access")
    except ClientError as e:
        logger.error(f"Failed to access QuickSight API: {str(e)}")
        raise

    csv_data = build_csv_data()
    if csv_data:
        output_path = write_to_s3(csv_data, fieldnames)
        logger.info(f"Job completed successfully. Output file: {output_path}")
    else:
        logger.warning("No data was generated. Check if there are any QuickSight topics in the account.")

except Exception as e:
    logger.error(f"Job failed with error: {str(e)}")
    raise