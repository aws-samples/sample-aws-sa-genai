import sys
import boto3
import csv
import io
import json
from datetime import datetime
from awsglue.utils import getResolvedOptions
# Get job parameters
args = getResolvedOptions(sys.argv, ['AWS_ACCOUNT_ID', 'S3_OUTPUT_PATH'])
account_id = args['AWS_ACCOUNT_ID']
s3_output_path = args['S3_OUTPUT_PATH']
# Clients
region = 'us-east-1'  # or your Q region
qs = boto3.client('quicksight', region_name=region)
s3 = boto3.client('s3')
# Get topics
def list_all_topics():
    topics = []
    next_token = None
    while True:
        params = {'AwsAccountId': account_id}
        if next_token:
            params['NextToken'] = next_token
        response = qs.list_topics(**params)
#        print("list_topic_response:", response['TopicsSummaries'])
        topics.extend(response['TopicsSummaries'])
        next_token = response.get('NextToken')
        if not next_token:
            break
#        print(topics)
    return topics
# Get detailed info
def describe_topics(topic_summaries):
    topic_details = []
    for summary in topic_summaries:
        topic_id = summary['TopicId']
        try:
            response = qs.describe_topic(
                AwsAccountId=account_id,
                TopicId=topic_id
            )
            topic = response.get('Topic',{})
            topic['TopicId'] = topic_id
            
            topic_details.append(topic)
            
        except Exception as e:
            print(f"Error describing topic {topic_id}: {e}")
    return topic_details
# Write to CSV in-memory and upload to S3
def write_csv_to_s3(topics):
    bucket = s3_output_path.replace("s3://", "").split('/')[0]
    key_prefix = '/'.join(s3_output_path.replace("s3://", "").split('/')[1:])
    # timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    s3_key = f"{key_prefix}/q_topics_info.csv"
    # Choose columns to include in the CSV
    fieldnames = ['TopicId', 'Name', 'DatasetArn','DatasetName', 'Description', 'UserExperienceVersion']
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for topic in topics:
        datasets = topic.get('DataSets', [])
        if not datasets:
            # Write a single row with empty DatasetArn if no datasets
            writer.writerow({
                'TopicId': topic.get('TopicId'),
                'Name': topic.get('Name'),
                'DatasetArn': '',
                'DatasetName': '',
                'Description': topic.get('Description', ''),
                'UserExperienceVersion': topic.get('UserExperienceVersion', '')
            })
        else:
            # Write one row per dataset
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
    print(f"CSV written to s3://{bucket}/{s3_key}")
# Main flow
def main():
    print("Listing Q Topics...")
    summaries = list_all_topics()
    print(f"Found {len(summaries)} topics.")
    print("Describing topics...")
    #print(summaries)
    detailed = describe_topics(summaries)
    print(" Writing CSV to S3...")
    write_csv_to_s3(detailed)
main()