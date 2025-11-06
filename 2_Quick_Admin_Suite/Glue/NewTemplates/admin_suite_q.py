import sys
import boto3
import csv
import io
import json
import logging
from datetime import datetime
from awsglue.utils import getResolvedOptions
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Get job parameters
args = getResolvedOptions(sys.argv, ['AWS_ACCOUNT_ID', 'AWS_REGION', 'S3_OUTPUT_PATH'])
account_id = args['AWS_ACCOUNT_ID']
region = args['AWS_REGION']
s3_output_path = args['S3_OUTPUT_PATH']

logger.info(f"Starting job with parameters: region={region}, account_id={account_id}, output_path={s3_output_path}")

# Initialize clients
qs = boto3.client('quicksight', region_name=region)
s3 = boto3.client('s3')

def list_all_topics():
    """Retrieve all QuickSight topics."""
    topics = []
    next_token = None
    while True:
        params = {'AwsAccountId': account_id}
        if next_token:
            params['NextToken'] = next_token
        response = qs.list_topics(**params)
        topics.extend(response['TopicsSummaries'])
        next_token = response.get('NextToken')
        if not next_token:
            break
    return topics

def describe_topic_details(topic_summaries):
    """Get detailed info for topics."""
    topic_details = []
    for summary in topic_summaries:
        topic_id = summary['TopicId']
        try:
            response = qs.describe_topic(
                AwsAccountId=account_id,
                TopicId=topic_id
            )
            topic = response.get('Topic', {})
            topic['TopicId'] = topic_id
            topic_details.append(topic)
        except Exception as e:
            logger.error(f"Error describing topic {topic_id}: {e}")
    return topic_details

def get_topic_permissions(topic_id):
    """Get permissions for a specific topic."""
    try:
        response = qs.describe_topic_permissions(
            AwsAccountId=account_id,
            TopicId=topic_id
        )
        return response.get('Permissions', [])
    except ClientError as e:
        logger.error(f"Error getting permissions for topic {topic_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting permissions for topic {topic_id}: {str(e)}")
        return []

def build_access_data(topics):
    """Build access CSV data from topics and permissions."""
    rows = []
    try:
        if not topics:
            logger.warning("No topics found in the account")
            return rows
            
        for topic in topics:
            topic_id = topic.get('TopicId')
            topic_name = topic.get('Name', '')
            logger.info(f"Processing topic permissions: {topic_name} (ID: {topic_id})")
            
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
        
        logger.info(f"Total access rows generated: {len(rows)}")
        return rows
        
    except Exception as e:
        logger.error(f"Error building access CSV data: {str(e)}")
        raise

def write_topics_info_to_s3(topics):
    """Write topic info CSV to S3."""
    bucket = s3_output_path.replace("s3://", "").split('/')[0]
    key_prefix = '/'.join(s3_output_path.replace("s3://", "").split('/')[1:])
    s3_key = f"{key_prefix}/q_topics_info/q_topics_info.csv"
    
    fieldnames = ['TopicId', 'Name', 'DatasetArn', 'DatasetName', 'Description', 'UserExperienceVersion']
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for topic in topics:
        datasets = topic.get('DataSets', [])
        if not datasets:
            writer.writerow({
                'TopicId': topic.get('TopicId'),
                'Name': topic.get('Name'),
                'DatasetArn': '',
                'DatasetName': '',
                'Description': topic.get('Description', ''),
                'UserExperienceVersion': topic.get('UserExperienceVersion', '')
            })
        else:
            for dataset in datasets:
                writer.writerow({
                    'TopicId': topic.get('TopicId'),
                    'Name': topic.get('Name'),
                    'DatasetArn': dataset["DatasetArn"],
                    'DatasetName': dataset.get('DatasetName', ''),
                    'Description': topic.get('Description', ''),
                    'UserExperienceVersion': topic.get('UserExperienceVersion', '')
                })
    
    s3.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=output.getvalue().encode('utf-8'),
        ContentType='text/csv'
    )
    logger.info(f"Topics info CSV written to s3://{bucket}/{s3_key}")

def write_access_to_s3(csv_data, fieldnames):
    """Write access CSV data to S3."""
    try:
        if not csv_data:
            logger.warning("No access data to write to CSV")
            return None

        # Create CSV in memory
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_data:
            writer.writerow(row)

        # Parse S3 path
        bucket_name = s3_output_path.replace("s3://", "").split('/')[0]
        prefix = "/".join(s3_output_path.replace("s3://", "").split('/')[1:])
        filename = f"{prefix}/q_object_access/q_object_access.csv"

        # Upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=csv_buffer.getvalue().encode('utf-8')
        )
        
        logger.info(f"Access CSV written to s3://{bucket_name}/{filename}")
        return f"s3://{bucket_name}/{filename}"
        
    except Exception as e:
        logger.error(f"Error writing access CSV to S3: {str(e)}")
        raise

def main():
    try:
        # Test QuickSight API access
        qs.list_topics(AwsAccountId=account_id)
        logger.info("Successfully verified QuickSight API access")
        
        # Get all topics
        logger.info("Listing Q Topics...")
        summaries = list_all_topics()
        logger.info(f"Found {len(summaries)} topics.")
        
        # Get detailed topic information
        logger.info("Describing topics...")
        detailed_topics = describe_topic_details(summaries)
        
        # Write topics info CSV
        logger.info("Writing topics info CSV to S3...")
        write_topics_info_to_s3(detailed_topics)
        
        # Build and write access data
        logger.info("Building access data...")
        access_fieldnames = [
            'AWS Account ID', 'Region', 'Asset Type',
            'Q Topic Name', 'Q Topic ID',
            'Permission granted', 'Owner Name',
            'ARN', 'Namespace',
            'permissions set'
        ]
        
        access_data = build_access_data(summaries)
        if access_data:
            write_access_to_s3(access_data, access_fieldnames)
            logger.info("Job completed successfully.")
        else:
            logger.warning("No access data was generated. Check if there are any QuickSight topics with permissions in the account.")
            
    except Exception as e:
        logger.error(f"Job failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    main()