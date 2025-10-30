# Import necessary libraries
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
args = getResolvedOptions(sys.argv, ['AWS_REGION'])
aws_region = args['AWS_REGION']
#quicksight_identity_region = args['QUICKSIGHT_IDENTITY_REGION']

# Initialize AWS clients
client = boto3.client('sns')
# Use QuickSight Identity Region for QuickSight client
client1 = boto3.client('quicksight', region_name=aws_region)
client2 = boto3.client('sts')

# Get AWS account ID
aws_account_id = client2.get_caller_identity()['Account']

# Set up S3 bucket information
s3 = boto3.resource('s3')
bucketname = 'admin-console-new-' + aws_account_id
bucket = s3.Bucket(bucketname)

# Define S3 key for the dataset info file
key = 'monitoring/quicksight/datasets_properties/datasets_properties.csv'

# Create a temporary directory and set up the local file name
tmpdir = tempfile.mkdtemp()
local_file_name = 'qs-datasets-info.csv'
path = os.path.join(tmpdir, local_file_name)

# Initialize list to store dataset access information
access = []
count = 0
next_token = None

# Main loop to process QuickSight datasets
while True:
   # List datasets, using pagination if necessary
   if next_token:
     response0 = client1.list_data_sets(AwsAccountId=aws_account_id,NextToken=next_token)
   else:
     response0 = client1.list_data_sets(AwsAccountId=aws_account_id)

   DataSetSummaries = response0["DataSetSummaries"]
   
   # Process each dataset
   for datasetid in DataSetSummaries:
     #if datasetid['Name'] not in ['Business Review', 'People Overview', 'Sales Pipeline','Web and Social Media Analytics']:
       DataSetId = datasetid["DataSetId"]
       count = count+1 
       Name = datasetid['Name']
       LastUpdatedTime = datasetid['LastUpdatedTime']
       ImportMode = datasetid['ImportMode']
       Arn = datasetid['Arn']
       region = Arn.split(":")[3]

       # Get dataset permissions
       response = client1.describe_data_set_permissions(DataSetId = DataSetId, AwsAccountId= aws_account_id)
       permissions = response['Permissions']

       # Process SPICE datasets
       if ImportMode == 'SPICE':
         response1 = client1.list_ingestions(DataSetId = DataSetId, AwsAccountId= aws_account_id)
         IngestionStatus = response1['Ingestions'][0]['IngestionStatus']
         RequestSource  = response1['Ingestions'][0]['RequestSource']
         RequestType  =  response1['Ingestions'][0]['RequestType']
         RefreshTriggeredTime = response1['Ingestions'][0]['CreatedTime']
         
         # Try to get consumed SPICE capacity
         try:
           response2 = client1.describe_data_set(DataSetId = DataSetId, AwsAccountId= aws_account_id)
           ConsumedSpiceCapacityInBytes = response2['DataSet']['ConsumedSpiceCapacityInBytes']
           Type = 'N'
         except Exception as e:
             try:
                response1 = client1.list_ingestions(DataSetId = DataSetId, AwsAccountId= aws_account_id)
                IngestionSizeInBytes =response1['Ingestions'][0]['IngestionSizeInBytes']
                ConsumedSpiceCapacityInBytes = IngestionSizeInBytes 
                Type = 'Y'
             except Exception as e:
                    response1 = client1.list_ingestions(DataSetId = DataSetId, AwsAccountId= aws_account_id)
                    IngestionStatus = response1['Ingestions'][0]['IngestionStatus']
                    if IngestionStatus == 'FAILED':
                     ConsumedSpiceCapacityInBytes = '0' 
                     Type = 'Y'
          
         # Process completed ingestions
         if IngestionStatus == 'COMPLETED':
           IngestionId = response1['Ingestions'][0]['IngestionId']
           RowsDropped  = response1['Ingestions'][0]['RowInfo']['RowsDropped']
           RowsIngested = response1['Ingestions'][0]['RowInfo']['RowsIngested']
           RefreshTimeinSeconds = response1['Ingestions'][0]['IngestionTimeInSeconds']
           
           # Process permissions for completed ingestions
           if permissions != []:
            for principal in permissions:
                actions = '|'.join(principal['Actions'])
                principal = principal['Principal'].split("/")
                ptype = principal[0].split(":")
                ptype = ptype[-1]
                additional_info = principal[-2]
                if len(principal)==4:
                  principal = principal[2]+'/'+principal[3]
                  access.append([region,DataSetId,Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, RowsIngested, 
                  RowsDropped, RefreshTriggeredTime, RefreshTimeinSeconds, RequestSource,
                  RequestType,IngestionStatus,'NoErrorInfoType', 'NoErrorInfoMessage',
                  ptype, principal, additional_info, actions,Type])
                elif len(principal)==3:
                    principal = principal[2]
                    access.append([region,DataSetId,Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, RowsIngested, 
                    RowsDropped, RefreshTriggeredTime, RefreshTimeinSeconds, RequestSource,
                    RequestType,IngestionStatus,'NoErrorInfoType', 'NoErrorInfoMessage',
                    ptype, principal, additional_info, actions,Type])
           elif permissions == []:
                 access.append([region,DataSetId,Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, RowsIngested, 
                  RowsDropped, RefreshTriggeredTime, RefreshTimeinSeconds, RequestSource,
                  RequestType,IngestionStatus,'NoErrorInfoType', 'NoErrorInfoMessage',
                  '', 'Orphaned', '', '',Type])

         # Process failed ingestions
         elif IngestionStatus == 'FAILED':
           IngestionId = response1['Ingestions'][0]['IngestionId']
           ErrorInfoType = response1['Ingestions'][0]['ErrorInfo']['Type']
           try:
            ErrorInfoMessage = response1['Ingestions'][0]['ErrorInfo']['Message']
           except Exception as e:
              ErrorInfoMessage = ''
           
           # Process permissions for failed ingestions
           if permissions != []:
            for principal in permissions:
                actions = '|'.join(principal['Actions'])
                principal = principal['Principal'].split("/")
                ptype = principal[0].split(":")
                ptype = ptype[-1]
                additional_info = principal[-2]
                if len(principal)==4:
                  principal = principal[2]+'/'+principal[3]
                  if len(ErrorInfoMessage) <= 100:
                       access.append([region,DataSetId, Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, '', 
                       '', RefreshTriggeredTime, '', RequestSource,
                        RequestType,IngestionStatus,ErrorInfoType,ErrorInfoMessage[0:50]+'-'+ "Please refer dataset refresh summary for complete error",
                        ptype, principal, additional_info, actions,Type])
                  elif len(ErrorInfoMessage) >= 100:
                        access.append([region,DataSetId, Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, '', '', RefreshTriggeredTime, '', RequestSource,
                              RequestType,IngestionStatus,ErrorInfoType, "Please refer dataset refresh summary for complete error",ptype, principal, additional_info, actions,Type])
                elif len(principal)==3:
                     principal = principal[2]
                     if len(ErrorInfoMessage) <= 100:
                       access.append([region,DataSetId, Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, '', 
                       '', RefreshTriggeredTime, '', RequestSource,
                        RequestType,IngestionStatus,ErrorInfoType,
                        ErrorInfoMessage[0:50]+'-'+ "Please refer dataset refresh summary for complete error",
                        ptype, principal, additional_info, actions,Type])
                     elif len(ErrorInfoMessage) >= 100:
                        access.append([region,DataSetId, Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, '', '', RefreshTriggeredTime, '', RequestSource,
                              RequestType,IngestionStatus,ErrorInfoType, "Please refer dataset refresh summary for complete error",
                              ptype, principal, additional_info, actions,Type])
           elif permissions == []:
               if len(ErrorInfoMessage) <= 100:
                      access.append([region,DataSetId, Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, '', 
                        '', RefreshTriggeredTime, '', RequestSource,
                         RequestType,IngestionStatus,ErrorInfoType,
                         ErrorInfoMessage[0:50]+'-'+ "Please refer dataset refresh summary for complete error",
                         '', 'Orphaned', '', '',Type])
               elif len(ErrorInfoMessage) >= 100:
                      access.append([region,DataSetId, Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, '', 
                           '', RefreshTriggeredTime, '', RequestSource,
                            RequestType,IngestionStatus,ErrorInfoType, 
                            "Please refer dataset refresh summary for complete error",
                            '', 'Orphaned', '', '',Type])
                 
         # Process other ingestion statuses (INITIALIZED, QUEUED, RUNNING, CANCELLED)
         elif IngestionStatus in ['INITIALIZED', 'QUEUED', 'RUNNING', 'CANCELLED']:
          if permissions != []:
              for principal in permissions:
                actions = '|'.join(principal['Actions'])
                principal = principal['Principal'].split("/")
                ptype = principal[0].split(":")
                ptype = ptype[-1]
                additional_info = principal[-2]
                if len(principal)==4:
                  principal = principal[2]+'/'+principal[3]
                  access.append([region,DataSetId,Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, '', 
                   '', RefreshTriggeredTime, '', RequestSource,
                    RequestType,IngestionStatus,'NoErrorInfoType', 'NoErrorInfoMessage',
                    ptype, principal, additional_info, actions,Type])
                elif len(principal)==3:
                     principal = principal[2]
                     access.append([region,DataSetId,Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, '', 
                     '', RefreshTriggeredTime, '', RequestSource,
                      RequestType,IngestionStatus,'NoErrorInfoType', 'NoErrorInfoMessage',
                      ptype, principal, additional_info, actions,Type])
          elif permissions == []:
                 access.append([region,DataSetId,Name , LastUpdatedTime, ImportMode,ConsumedSpiceCapacityInBytes, '', 
                      '', RefreshTriggeredTime, '', RequestSource,
                      RequestType,IngestionStatus,'NoErrorInfoType', 'NoErrorInfoMessage',
                      '', 'Orphaned', '', '',Type])
         
       # Process DIRECT_QUERY datasets
       elif ImportMode == 'DIRECT_QUERY':
        if permissions != []:
         for principal in permissions:
                actions = '|'.join(principal['Actions'])
                principal = principal['Principal'].split("/")
                ptype = principal[0].split(":")
                ptype = ptype[-1]
                additional_info = principal[-2]
                if len(principal)==4:
                  principal = principal[2]+'/'+principal[3]
                  access.append([region,DataSetId,Name , LastUpdatedTime,ImportMode,'0',
                  '','','','',
                  '','', '', 'NoErrorInfoType', 'NoErrorInfoMessage',
                  ptype, principal, additional_info, actions,''])
                elif len(principal)==3:
                     principal = principal[2]
                     access.append([region,DataSetId,Name , LastUpdatedTime,ImportMode,'0','',
                     '','','','',
                     '','','','NoErrorInfoType', 'NoErrorInfoMessage',
                      ptype, principal, additional_info, actions,''])
        elif permissions == []:
                 access.append([region,DataSetId,Name , LastUpdatedTime,ImportMode,'0','',
                     '','','','',
                     '','','','NoErrorInfoType', 'NoErrorInfoMessage',
                     '', 'Orphaned', '', '',''])
                     
   # Check for more datasets to process (pagination)
   next_token = response0.get('NextToken', None)
   if next_token is None:
    break

# Define column titles for the CSV file
column_titles = ['Region','DataSetID', 'Name', 'LastUpdatedTime', 'ImportMode', 'ConsumedSPICECapacityinBytes', 'RowsIngested', 'RowsDropped', 'RefreshTriggeredTime', 'RefreshTimeinSeconds', 'RequestSource', 'RequestType', 'IngestionStatus', 'ErrorInfoType', 'ErrorInfoMessage', 'PrincipalType', 'Principal', 'AdditionalInfo', 'Actions','IsFile']                     

# Write the dataset information to a CSV file
with open(path, 'w', newline='') as outfile:
 writer = csv.writer(outfile, delimiter=',')
 writer.writerow(column_titles)
 for line in access:
  writer.writerow(line)
outfile.close()

# Upload the CSV file to S3
bucket.upload_file(path, key)
