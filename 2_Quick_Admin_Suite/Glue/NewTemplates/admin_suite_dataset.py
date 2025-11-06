import json
import boto3
import logging
import csv
import io
import os
import tempfile
from typing import Any, Callable, Dict, List, Optional, Union
import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from awsglue.job import Job
import botocore

# Configure botocore and boto3 logging
def default_botocore_config() -> botocore.config.Config:
    """Botocore configuration."""
    retries_config: Dict[str, Union[str, int]] = {
        "max_attempts": int(os.getenv("AWS_MAX_ATTEMPTS", "5")),
    }
    mode: Optional[str] = os.getenv("AWS_RETRY_MODE")
    if mode:
        retries_config["mode"] = mode
    return botocore.config.Config(
        retries=retries_config,
        connect_timeout=10,
        max_pool_connections=10,
        user_agent_extra=f"qs_sdk_admin_console",
    )

# Initialize Spark and Glue contexts
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# Set up client and region
sts_client = boto3.client("sts", config=default_botocore_config())
account_id = sts_client.get_caller_identity()["Account"]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'AWS_REGION', 'S3_OUTPUT_PATH'])
job.init(args['JOB_NAME'], args)
aws_region = args['AWS_REGION']
s3_output_path = args['S3_OUTPUT_PATH']
qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())

# define the _list function to handle pagination and return a list of resources
def _list(
        func_name: str,
        attr_name: str,
        account_id: str,
        aws_region: str,
        **kwargs, ) -> List[Dict[str, Any]]:
    func: Callable = getattr(qs_client, func_name)
    response = func(AwsAccountId=account_id, **kwargs)
    next_token: str = response.get("NextToken", None)
    result: List[Dict[str, Any]] = response[attr_name]
    while next_token is not None:
        response = func(AwsAccountId=account_id, NextToken=next_token, **kwargs)
        next_token = response.get("NextToken", None)
        result += response[attr_name]
    return result

def list_dashboards(account_id, aws_region) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_dashboards",
        attr_name="DashboardSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )

def list_datasets(account_id, aws_region) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_data_sets",
        attr_name="DataSetSummaries",
        account_id=account_id,
        aws_region=aws_region
    )

def describe_dashboard(account_id, dashboardid, aws_region):
    res = qs_client.describe_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res

def describe_analysis(account_id, id, aws_region):
    res = qs_client.describe_analysis(
        AwsAccountId=account_id,
        AnalysisId=id
    )
    return res

def describe_data_set(account_id, id, aws_region):
    res = qs_client.describe_data_set(
        AwsAccountId=account_id,
        DataSetId=id
    )
    return res

def describe_data_source(account_id, id, aws_region):
    res = qs_client.describe_data_source(
        AwsAccountId=account_id,
        DataSourceId=id
    )
    return res

def get_s3_bucket_name_from_path(s3_path: str) -> str:
    """Extract S3 bucket name from S3 path."""
    return s3_path.replace('s3://', '').split('/')[0]

if __name__ == "__main__":
    # Create S3 resource
    s3 = boto3.resource('s3')
    bucketname = get_s3_bucket_name_from_path(s3_output_path)
    bucket = s3.Bucket(bucketname)

    # Check if bucket exists
    try:
        bucket.load()
        print(f"Bucket {bucketname} exists.")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Bucket {bucketname} does not exist. Please create the bucket before running this script.")
            sys.exit(1)
        else:
            raise e
    
    # Create temporary directory and file paths
    s3_prefix = '/'.join(s3_output_path.replace('s3://', '').split('/')[1:])
    tmpdir = tempfile.mkdtemp()
    
    # File paths for outputs
    datasets_info_key = f'{s3_prefix}/datasets_info/datasets_info.csv'
    data_dictionary_key = f'{s3_prefix}/data_dictionary/data_dictionary.csv'
    datasets_properties_key = f'{s3_prefix}/datasets_properties/datasets_properties.csv'
    
    datasets_info_path = os.path.join(tmpdir, 'datasets_info.csv')
    data_dictionary_path = os.path.join(tmpdir, 'data_dictionary.csv')
    datasets_properties_path = os.path.join(tmpdir, 'datasets_properties.csv')

    # Initialize data collections
    datasets_info = []
    data_dictionary = []
    datasets_properties = []

    # Process dashboards for lineage information
    dashboards = list_dashboards(account_id, aws_region)
    for dashboard in dashboards:
        dashboardid = dashboard['DashboardId']
        response = describe_dashboard(account_id, dashboardid, aws_region)
        Dashboard = response['Dashboard']
        Name = Dashboard['Name']
        
        print(Name)
        if 'SourceEntityArn' in Dashboard['Version']:
            SourceEntityArn = Dashboard['Version']['SourceEntityArn']
            SourceType = SourceEntityArn.split(":")[-1].split("/")[0]
            if SourceType == 'analysis':
                Sourceid = SourceEntityArn.split("/")[-1]
                try:
                    Source = describe_analysis(account_id, Sourceid, aws_region)
                    SourceName = Source['Analysis']['Name']
                except botocore.exceptions.ClientError as error:
                    if error.response['Error']['Code'] == 'ResourceNotFoundException':
                        print("Analysis ID: " + Sourceid + " not found/does not exist in your account.")
                        Sourceid = 'N/A'
                        SourceName = 'N/A'
                    else:
                        raise error
            else:
                Sourceid = 'N/A'
                SourceName = 'N/A'
        else:
            Sourceid = 'N/A'
            SourceName = 'N/A'
            
        # Get the datasets for the dashboard
        DataSetArns = Dashboard['Version']['DataSetArns']
        for ds in DataSetArns:
            dsid = ds.split("/")[-1]
            try:
                dataset = describe_data_set(account_id, dsid, aws_region)
                dsname = dataset['DataSet']['Name']
                LastUpdatedTime = dataset['DataSet']['LastUpdatedTime']
                PhysicalTableMap = dataset['DataSet']['PhysicalTableMap']
                
                for sql in PhysicalTableMap:
                    sql = PhysicalTableMap[sql]
                    if 'RelationalTable' in sql:
                        DataSourceArn = sql['RelationalTable']['DataSourceArn']
                        DataSourceid = DataSourceArn.split("/")[-1]
                        try:
                            datasource = describe_data_source(account_id, DataSourceid, aws_region)
                            datasourcename = datasource['DataSource']['Name']
                        except botocore.exceptions.ClientError as error:
                            if error.response['Error']['Code'] == 'ResourceNotFoundException':
                                DataSourceid = 'N/A'
                                datasourcename = 'N/A'
                            else:
                                raise error
                        
                        Catalog = sql['RelationalTable'].get('Catalog', 'N/A')
                        Schema = sql['RelationalTable'].get('Schema', 'N/A')
                        sqlName = sql['RelationalTable'].get('Name', 'N/A')

                        datasets_info.append([aws_region, Name, dashboardid, SourceName, Sourceid, dsname, dsid, LastUpdatedTime,
                                             datasourcename, DataSourceid, Catalog, Schema, sqlName])

                    if 'CustomSql' in sql:
                        DataSourceArn = sql['CustomSql']['DataSourceArn']
                        DataSourceid = DataSourceArn.split("/")[-1]
                        try:
                            datasource = describe_data_source(account_id, DataSourceid, aws_region)
                            datasourcename = datasource['DataSource']['Name']
                        except botocore.exceptions.ClientError as error:
                            if error.response['Error']['Code'] == 'ResourceNotFoundException':
                                DataSourceid = 'N/A'
                                datasourcename = 'N/A'
                            else:
                                raise error
                        
                        SqlQuery = sql['CustomSql']['SqlQuery'].replace("\n", "").replace("\r", "").replace("\t", "")
                        sqlName = sql['CustomSql']['Name']

                        datasets_info.append([aws_region, Name, dashboardid, SourceName, Sourceid, dsname, dsid, LastUpdatedTime,
                                             datasourcename, DataSourceid, 'N/A', sqlName, SqlQuery])

            except botocore.exceptions.ClientError as error:
                if error.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"Dataset ID: " + dsid + " not found/does not exist in your account. Skipping this dataset.")
                    continue
            except Exception as e:
                if (str(e).find('flat file') != -1):
                    pass
                else:
                    raise e

    # Process datasets for properties and data dictionary
    datasets = list_datasets(account_id, aws_region)
    next_token = None
    
    while True:
        if next_token:
            response0 = qs_client.list_data_sets(AwsAccountId=account_id, NextToken=next_token)
        else:
            response0 = qs_client.list_data_sets(AwsAccountId=account_id)

        DataSetSummaries = response0["DataSetSummaries"]
        
        for datasetid in DataSetSummaries:
            DataSetId = datasetid["DataSetId"]
            Name = datasetid['Name']
            LastUpdatedTime = datasetid['LastUpdatedTime']
            ImportMode = datasetid['ImportMode']
            Arn = datasetid['Arn']
            region = Arn.split(":")[3]

            try:
                # Get dataset details for data dictionary
                dataset_details = describe_data_set(account_id, DataSetId, aws_region)
                OutputColumns = dataset_details['DataSet']['OutputColumns']
                for column in OutputColumns:
                    columnname = column['Name']
                    columntype = column['Type']
                    columndesc = column.get('Description', None)
                    data_dictionary.append([Name, DataSetId, columnname, columntype, columndesc])

                # Process SPICE datasets for properties
                if ImportMode == 'SPICE':
                    response1 = qs_client.list_ingestions(DataSetId=DataSetId, AwsAccountId=account_id)
                    if not response1['Ingestions']:
                        print(f"No ingestions found for dataset {DataSetId}. Skipping.")
                        continue
                    IngestionStatus = response1['Ingestions'][0]['IngestionStatus']
                    RequestSource = response1['Ingestions'][0]['RequestSource']
                    RequestType = response1['Ingestions'][0]['RequestType']
                    RefreshTriggeredTime = response1['Ingestions'][0]['CreatedTime']
                    
                    # Try to get consumed SPICE capacity
                    try:
                        response2 = qs_client.describe_data_set(DataSetId=DataSetId, AwsAccountId=account_id)
                        ConsumedSpiceCapacityInBytes = response2['DataSet']['ConsumedSpiceCapacityInBytes']
                        Type = 'N'
                    except Exception as e:
                        try:
                            IngestionSizeInBytes = response1['Ingestions'][0]['IngestionSizeInBytes']
                            ConsumedSpiceCapacityInBytes = IngestionSizeInBytes
                            Type = 'Y'
                        except Exception as e:
                            if IngestionStatus == 'FAILED':
                                ConsumedSpiceCapacityInBytes = '0'
                                Type = 'Y'
                    
                    # Process completed ingestions
                    if IngestionStatus == 'COMPLETED':
                        row_info = response1['Ingestions'][0].get('RowInfo', {})
                        RowsDropped = row_info.get('RowsDropped', 0)
                        RowsIngested = row_info.get('RowsIngested', 0)
                        RefreshTimeinSeconds = response1['Ingestions'][0].get('IngestionTimeInSeconds', 0)
                        
                        datasets_properties.append([region, DataSetId, Name, LastUpdatedTime, ImportMode, ConsumedSpiceCapacityInBytes, 
                                                   RowsIngested, RowsDropped, RefreshTriggeredTime, RefreshTimeinSeconds, RequestSource,
                                                   RequestType, IngestionStatus, 'NoErrorInfoType', 'NoErrorInfoMessage', Type])

                    # Process failed ingestions
                    elif IngestionStatus == 'FAILED':
                        ErrorInfoType = response1['Ingestions'][0]['ErrorInfo']['Type']
                        ErrorInfoMessage = response1['Ingestions'][0]['ErrorInfo'].get('Message', '')
                        error_msg = ErrorInfoMessage[0:50] + '-Please refer dataset refresh summary for complete error' if len(ErrorInfoMessage) <= 100 else "Please refer dataset refresh summary for complete error"
                        
                        datasets_properties.append([region, DataSetId, Name, LastUpdatedTime, ImportMode, ConsumedSpiceCapacityInBytes, 
                                                   '', '', RefreshTriggeredTime, '', RequestSource, RequestType, IngestionStatus, 
                                                   ErrorInfoType, error_msg, Type])

                    # Process other ingestion statuses
                    elif IngestionStatus in ['INITIALIZED', 'QUEUED', 'RUNNING', 'CANCELLED']:
                        datasets_properties.append([region, DataSetId, Name, LastUpdatedTime, ImportMode, ConsumedSpiceCapacityInBytes, 
                                                   '', '', RefreshTriggeredTime, '', RequestSource, RequestType, IngestionStatus, 
                                                   'NoErrorInfoType', 'NoErrorInfoMessage', Type])

                # Process DIRECT_QUERY datasets
                elif ImportMode == 'DIRECT_QUERY':
                    datasets_properties.append([region, DataSetId, Name, LastUpdatedTime, ImportMode, '0', '', '', '', '', '', '', '', 
                                               'NoErrorInfoType', 'NoErrorInfoMessage', ''])

            except botocore.exceptions.ClientError as error:
                if error.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"Dataset ID: " + DataSetId + " not found/does not exist in your account. Skipping this dataset.")
                    continue
            except Exception as e:
                if (str(e).find('data set type is not supported') != -1):
                    pass
                else:
                    raise e

        # Check for more datasets to process (pagination)
        next_token = response0.get('NextToken', None)
        if next_token is None:
            break

    # Write datasets_info to CSV
    with open(datasets_info_path, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter='|')
        for line in datasets_info:
            writer.writerow(line)
    bucket.upload_file(datasets_info_path, datasets_info_key)

    # Write data_dictionary to CSV
    with open(data_dictionary_path, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for line in data_dictionary:
            writer.writerow(line)
    bucket.upload_file(data_dictionary_path, data_dictionary_key)

    # Write datasets_properties to CSV
    column_titles = ['Region', 'DataSetID', 'Name', 'LastUpdatedTime', 'ImportMode', 'ConsumedSPICECapacityinBytes', 
                     'RowsIngested', 'RowsDropped', 'RefreshTriggeredTime', 'RefreshTimeinSeconds', 'RequestSource', 
                     'RequestType', 'IngestionStatus', 'ErrorInfoType', 'ErrorInfoMessage', 'IsFile']
    
    with open(datasets_properties_path, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        writer.writerow(column_titles)
        for line in datasets_properties:
            writer.writerow(line)
    bucket.upload_file(datasets_properties_path, datasets_properties_key)

    print("Combined dataset processing completed successfully.")
    
    # Commit the job
    job.commit()