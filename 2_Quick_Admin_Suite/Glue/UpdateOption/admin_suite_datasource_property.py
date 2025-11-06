# Import required libraries for AWS services, file handling, and data processing
import base64
import json
import boto3
import os
import sys
import pprint
import datetime
from datetime import datetime, date, time, timezone
import logging
import csv
import io
import tempfile
from awsglue.utils import getResolvedOptions
import botocore

# Get AWS region and QuickSight Identity Region from Glue job parameters
args = getResolvedOptions(sys.argv, ['AWS_REGION', 'QUICKSIGHT_IDENTITY_REGION', 'S3_OUTPUT_PATH'])
aws_region = args['AWS_REGION']
quicksight_identity_region = args['QUICKSIGHT_IDENTITY_REGION']
s3_output_path = args['S3_OUTPUT_PATH']

# Initialize AWS service clients for SNS, QuickSight and STS
client = boto3.client('sns')
# Use QuickSight Identity Region for QuickSight client
client1 = boto3.client('quicksight', region_name=aws_region)
client2 = boto3.client('sts')
aws_account_id = client2.get_caller_identity()['Account']

# Initialize S3 resource and set up bucket name
s3 = boto3.resource('s3')
bucketname = s3_output_path.replace('s3://', '').split('/')[0]
bucket = s3.Bucket(bucketname)

# Define S3 key paths for storing different QuickSight information
s3_prefix = '/'.join(s3_output_path.replace('s3://', '').split('/')[1:])
key = f'{s3_prefix}/datasource_property.csv'

# Create temporary directory and file path for processing
tmpdir = tempfile.mkdtemp()
local_file_name = 'qs-datasource-info.csv'
path = os.path.join(tmpdir, local_file_name)

# Initialize list to store datasource dependencies and pagination token
datasourcedependent = []
next_token = None
   
# Main loop to process all datasets
while True:
   # Handle pagination for listing datasets
   if next_token:
     response4 = client1.list_data_sets(AwsAccountId=aws_account_id,NextToken=next_token)
   else:
     response4 = client1.list_data_sets(AwsAccountId=aws_account_id)
   datasets = response4['DataSetSummaries']

   # Process each dataset
   for dataset in datasets:
     DataSetId = dataset['DataSetId']
     try:
                # Get detailed information about the dataset
                response5 = client1.describe_data_set(AwsAccountId=aws_account_id, DataSetId= DataSetId)
                dsname = response5['DataSet']['Name']
                print(dsname)
                datasetLastUpdatedTime = response5['DataSet']['LastUpdatedTime']
                print(datasetLastUpdatedTime)
                datasetCreatedTime = response5['DataSet']['CreatedTime']
                PhysicalTableMap = response5['DataSet']['PhysicalTableMap']
                print(PhysicalTableMap)

                # Process each table in the physical table map
                for sql in PhysicalTableMap:
                    sql = PhysicalTableMap[sql]

                    # Handle RelationalTable type datasource
                    if 'RelationalTable' in sql:
                        DataSourceArn = sql['RelationalTable']['DataSourceArn']
                        DataSourceid = DataSourceArn.split("/")
                        DataSourceid = DataSourceid[-1]
                        try:
                           datasource = client1.describe_data_source(AwsAccountId=aws_account_id, DataSourceId=DataSourceid)
                           datasourcename = datasource['DataSource']['Name']
                           Type = datasource['DataSource']['Type']
                           datasourcedependent.append(
                            [aws_region,datasourcename, DataSourceid, dsname,Type, DataSetId, datasetLastUpdatedTime,datasetCreatedTime])
                        except Exception as e:
                            datasourcedependent.append(
                            [aws_region,'Not-found', DataSourceid, dsname, 'Not-found', DataSetId, datasetLastUpdatedTime,datasetCreatedTime])
                        
                    # Handle CustomSQL type datasource
                    if 'CustomSql' in sql:
                        DataSourceArn = sql['CustomSql']['DataSourceArn']
                        DataSourceid = DataSourceArn.split("/")
                        DataSourceid = DataSourceid[-1]
                        try:
                            datasource = client1.describe_data_source(AwsAccountId=aws_account_id, DataSourceId=DataSourceid)
                            datasourcename = datasource['DataSource']['Name']
                            Type = datasource['DataSource']['Type']
                            datasourcedependent.append(
                                [aws_region,datasourcename, DataSourceid, dsname,Type, DataSetId, datasetLastUpdatedTime,datasetCreatedTime])
                        except Exception as e:
                            datasourcedependent.append(
                            [aws_region,'Not-found', DataSourceid, dsname, 'Not-found', DataSetId, datasetLastUpdatedTime,datasetCreatedTime])
                        
                    # Handle S3Source type datasource
                    if 'S3Source' in sql:
                        DataSourceArn = sql['S3Source']['DataSourceArn']
                        DataSourceid = DataSourceArn.split("/")
                        DataSourceid = DataSourceid[-1]
                        try:
                            datasource = client1.describe_data_source(AwsAccountId=aws_account_id, DataSourceId=DataSourceid)
                            datasourcename = datasource['DataSource']['Name']
                            Type = datasource['DataSource']['Type']
 
                            datasourcedependent.append(
                            [aws_region,datasourcename, DataSourceid, dsname,Type, DataSetId, datasetLastUpdatedTime,datasetCreatedTime])
                        except Exception as e:
                            datasourcedependent.append(
                            [aws_region,'Not-found', DataSourceid, dsname, 'Not-found', DataSetId, datasetLastUpdatedTime,datasetCreatedTime])
                    
     # Handle exceptions for unsupported dataset types                   
     except Exception as e:
              if str(e).find('data set type is not supported'):
                pass
                token = None
                # Handle file-type datasets
                while True:
                   if token:
                       response00 = client1.list_data_sets(AwsAccountId=aws_account_id,NextToken=token)
                   else:
                      response00= client1.list_data_sets(AwsAccountId=aws_account_id)
                   count = -1
                   DataSetSummaries = response00["DataSetSummaries"]
                   for datasetid in DataSetSummaries:
                         dsid = datasetid["DataSetId"]
                         count=count+1
                         if  dsid == DataSetId :
                           dsname = response00["DataSetSummaries"][count]['Name']
                           datasetLastUpdatedTime = response00["DataSetSummaries"][count]['LastUpdatedTime']
                           datasetCreatedTime = response00["DataSetSummaries"][count]['CreatedTime']
                           count = -1
                           datasourcedependent.append(
                            [aws_region,'N/A', 'N/A', dsname, 'File type', DataSetId, datasetLastUpdatedTime,datasetCreatedTime])
                           break
                   token = response00.get('NextToken', None)
                   if token is None:
                     break
              else:
                raise e
   
   # Check for more datasets to process (pagination)
   next_token = response4.get('NextToken', None)
   if next_token is None:
    break
   
# Define column titles for the CSV output
column_titles = ['Region', 'DataSourceName', 'DataSourceID', 'DatasetName', 'DataSourceType', 'DatasetID', 'DatasetLastUpdatedTime', 'DatasetCreatedTime']

# Write data to CSV file
try:
    with open(path, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        writer.writerow(column_titles)
        for line in datasourcedependent:
            writer.writerow(line)
except IOError as e:
    print(f"Error writing CSV file: {e}")
    raise

# Upload CSV file to S3
try:
    bucket.upload_file(path, key)
except botocore.exceptions.ClientError as e:
    print(f"Error uploading to S3: {e}")
    raise   