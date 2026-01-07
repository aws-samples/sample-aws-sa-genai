import json
import boto3
import logging
import csv
import io
import os
import tempfile
import time
import random
from typing import Any, Callable, Dict, List, Optional, Union
import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from awsglue.job import Job
import botocore
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def call_with_backoff(api_func: Callable, max_retries: int = 10, **kwargs):
    """Call a boto3 API with exponential backoff + jitter for throttling."""
    for attempt in range(max_retries):
        try:
            return api_func(**kwargs)
        except botocore.exceptions.ClientError as e:
            code = e.response['Error']['Code']
            if code == 'ThrottlingException':
                delay = min((2 ** attempt) + random.uniform(0, 1), 60)
                print(f"Throttled on {api_func.__name__}, sleeping {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError(f"Failed after {max_retries} retries due to throttling: {api_func.__name__}")

#start-Initial set up for the sdk env#
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
#end-Initial set up for the sdk env#

#start-Initial set up for the glue and qs client of boto3#
# Initialize Spark and Glue contexts
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

sts_client = boto3.client("sts", config=default_botocore_config())
account_id = sts_client.get_caller_identity()["Account"]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'AWS_REGION', 'S3_OUTPUT_PATH'])
job.init(args['JOB_NAME'], args)
print('region', args['AWS_REGION'])
aws_region = args['AWS_REGION']
glue_aws_region = args['AWS_REGION']
s3_output_path = args['S3_OUTPUT_PATH']
qs_client = boto3.client('quicksight', config=default_botocore_config())
qs_local_client = boto3.client('quicksight', region_name=glue_aws_region, config=default_botocore_config())

print(glue_aws_region)

ssm = boto3.client('ssm', region_name=glue_aws_region, config=default_botocore_config())
#end-Initial set up for the glue and qs client of boto3#

#start-advanced settings for ssm usage of qs-configuration#
#optional for this use case#
"""
def get_ssm_parameters(ssm_string):
    config_str = ssm.get_parameter(
        Name=ssm_string
    )['Parameter']['Value']
    return json.loads(config_str)


def get_s3_info(account_id, glue_aws_region):
    bucket_name = get_ssm_parameters('/qs/config/groups')
    bucket_name = bucket_name['bucket-name']
    return bucket_name
"""
#end-advanced settings for ssm usage of qs-configuration#

#parent class of list* functions
def _list(
        func_name: str,
        attr_name: str,
        account_id: str,
        aws_region: str,
        **kwargs, ) -> List[Dict[str, Any]]:
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    func: Callable = getattr(qs_client, func_name)
    response = func(AwsAccountId=account_id, **kwargs)
    next_token: str = response.get("NextToken", None)
    result: List[Dict[str, Any]] = response[attr_name]
    while next_token is not None:
        response = func(AwsAccountId=account_id, NextToken=next_token, **kwargs)
        next_token = response.get("NextToken", None)
        result += response[attr_name]
    return result

#start-user related list* functions#
def list_group_memberships(
        group_name: str,
        account_id: str,
        aws_region: str,
        namespace: str = "default"
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_group_memberships",
        attr_name="GroupMemberList",
        account_id=account_id,
        GroupName=group_name,
        Namespace=namespace,
        aws_region=aws_region
    )


def list_users(account_id, aws_region, ns) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_users",
        attr_name="UserList",
        Namespace=ns,
        account_id=account_id,
        aws_region=aws_region
    )



def list_groups(
        account_id, aws_region, ns
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_groups",
        attr_name="GroupList",
        Namespace=ns,
        account_id=account_id,
        aws_region=aws_region
    )


def list_user_groups(UserName, account_id, aws_region, ns) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_user_groups",
        attr_name="GroupList",
        Namespace=ns,
        UserName=UserName,
        account_id=account_id,
        aws_region=aws_region
    )


def list_namespaces(
        account_id, aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_namespaces",
        attr_name="Namespaces",
        account_id=account_id,
        aws_region=aws_region
    )
#end-user related list* functions#

#start-assets related list* functions#
def list_dashboards(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_dashboards",
        attr_name="DashboardSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )

def list_analyses(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_analyses",
        attr_name="AnalysisSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )

def list_themes(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_themes",
        attr_name="ThemeSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )

def list_datasets(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_data_sets",
        attr_name="DataSetSummaries",
        account_id=account_id,
        aws_region=aws_region
    )


def list_datasources(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_data_sources",
        attr_name="DataSources",
        account_id=account_id,
        aws_region=aws_region
    )

def list_ingestions(
        account_id,
        aws_region,
        DataSetId
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_ingestions",
        attr_name="Ingestions",
        account_id=account_id,
        aws_region=aws_region,
        DataSetId=DataSetId
    )


def list_folders(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_folders",
        attr_name="FolderSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )


def list_folder_members(
        account_id,
        aws_region,
        folderid
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_folder_members",
        attr_name="FolderMemberList",
        account_id=account_id,
        aws_region=aws_region,
        FolderId=folderid
    )


def list_topics(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_topics",
        attr_name="TopicsSummaries",
        account_id=account_id,
        aws_region=aws_region
)

#parent class of describe* functions
def _describe(
        func_name: str,
        attr_name: str,
        account_id: str,
        aws_region: str,
        **kwargs, ) -> List[Dict[str, Any]]:
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    func: Callable = getattr(qs_client, func_name)
    response = func(AwsAccountId=account_id, **kwargs)
    result = response[attr_name]
    return result


#start-assets management describe functions
def describe_folder(
        account_id,
        id,
        aws_region) -> Dict[str, Any]:
    return _describe(
        func_name="describe_folder",
        attr_name="Folder",
        account_id=account_id,
        aws_region=aws_region,
        FolderId=id
    )

def describe_dashboard(account_id, dashboardid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res


def describe_analysis(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_analysis(
        AwsAccountId=account_id,
        AnalysisId=id
    )
    return res


def describe_data_set(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_data_set(
        AwsAccountId=account_id,
        DataSetId=id
    )
    return res


def describe_data_source(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_data_source(
        AwsAccountId=account_id,
        DataSourceId=id
    )
    return res
#end-assets management describe functions

#start-access control related describe functions
def describe_folder_permissions(
        account_id,
        id,
        aws_region) -> Dict[str, Any]:
    return _describe(
        func_name="describe_folder_permissions",
        attr_name="Permissions",
        account_id=account_id,
        aws_region=aws_region,
        FolderId=id
    )


def describe_dashboard_permissions(
    account_id,
    dashboardid,
    aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_dashboard_permissions(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res

def describe_analysis_permissions(account_id, aid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_analysis_permissions(
        AwsAccountId=account_id,
        AnalysisId=aid
    )
    return res

def describe_theme_permissions(account_id, aid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_theme_permissions(
        AwsAccountId=account_id,
        ThemeId=aid
    )
    return res



def describe_data_set_permissions(account_id, datasetid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_data_set_permissions(
        AwsAccountId=account_id,
        DataSetId=datasetid
    )
    return res


def describe_data_source_permissions(account_id, DataSourceId, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_data_source_permissions(
        AwsAccountId=account_id,
        DataSourceId=DataSourceId
    )
    return res
def process_dashboard_permissions(dashboard):
    """Process permissions for a single dashboard"""
    try:
        response = call_with_backoff(lambda: describe_dashboard_permissions(account_id, dashboard['DashboardId'], glue_aws_region))
        permissions = response['Permissions']
        results = []
        
        for principal in permissions:
            actions = '|'.join(principal['Actions'])
            arn = principal['Principal']
            principal_parts = principal['Principal'].split("/")
            ptype = principal_parts[0].split(":")[-1]
            additional_info = principal_parts[1] if len(principal_parts) > 1 else ""
            
            if len(principal_parts)==4:
                principal_name = principal_parts[2]+'/'+principal_parts[3]
            elif len(principal_parts)==3:
                principal_name = principal_parts[2]
            else:
                principal_name = principal_parts[1] if len(principal_parts) > 1 else ""
            
            results.append([account_id, glue_aws_region, 'dashboard', dashboard['Name'], 
                          dashboard['DashboardId'], ptype, principal_name, arn, additional_info, actions])
        return results
    except Exception as e:
        print(f"Error processing dashboard {dashboard['DashboardId']}: {e}")
        return []

def process_dataset_permissions(dataset):
    """Process permissions for a single dataset"""
    if dataset['Name'] in ['Business Review', 'People Overview', 'Sales Pipeline', 'Web and Social Media Analytics']:
        return []
    
    try:
        response = call_with_backoff(lambda: describe_data_set_permissions(account_id, dataset['DataSetId'], glue_aws_region))
        permissions = response['Permissions']
        results = []
        
        for principal in permissions:
            actions = '|'.join(principal['Actions'])
            arn = principal['Principal']
            principal_parts = principal['Principal'].split("/")
            ptype = principal_parts[0].split(":")[-1]
            additional_info = principal_parts[-2] if len(principal_parts) > 2 else ""
            
            if len(principal_parts)==4:
                principal_name = principal_parts[2]+'/'+principal_parts[3]
            elif len(principal_parts)==3:
                principal_name = principal_parts[2]
            else:
                principal_name = principal_parts[1] if len(principal_parts) > 1 else ""
            
            results.append([account_id, glue_aws_region, 'dataset', dataset['Name'], 
                          dataset['DataSetId'], ptype, principal_name, arn, additional_info, actions])
        return results
    except Exception as e:
        print(f"Error processing dataset {dataset['DataSetId']}: {e}")
        return []

def process_datasource_permissions(datasource):
    """Process permissions for a single datasource"""
    if datasource['Name'] in ['Business Review', 'People Overview', 'Sales Pipeline', 'Web and Social Media Analytics']:
        return []
    
    if 'DataSourceParameters' not in datasource:
        return []
    
    try:
        response = call_with_backoff(lambda: describe_data_source_permissions(account_id, datasource['DataSourceId'], glue_aws_region))
        permissions = response['Permissions']
        results = []
        
        for principal in permissions:
            actions = '|'.join(principal['Actions'])
            arn = principal['Principal']
            principal_parts = principal['Principal'].split("/")
            ptype = principal_parts[0].split(":")[-1]
            additional_info = principal_parts[-2] if len(principal_parts) > 2 else ""
            
            if len(principal_parts)==4:
                principal_name = principal_parts[2]+'/'+principal_parts[3]
            elif len(principal_parts)==3:
                principal_name = principal_parts[2]
            else:
                principal_name = principal_parts[1] if len(principal_parts) > 1 else ""
            
            results.append([account_id, glue_aws_region, 'data_source', datasource['Name'], 
                          datasource['DataSourceId'], ptype, principal_name, arn, additional_info, actions])
        return results
    except Exception as e:
        print(f"Error processing datasource {datasource['DataSourceId']}: {e}")
        return []

def process_analysis_permissions(analysis):
    """Process permissions for a single analysis"""
    if analysis['Status'] == 'DELETED':
        return []
    
    try:
        response = call_with_backoff(lambda: describe_analysis_permissions(account_id, analysis['AnalysisId'], glue_aws_region))
        permissions = response['Permissions']
        results = []
        
        for principal in permissions:
            actions = '|'.join(principal['Actions'])
            arn = principal['Principal']
            principal_parts = principal['Principal'].split("/")
            ptype = principal_parts[0].split(":")[-1]
            additional_info = principal_parts[-2] if len(principal_parts) > 2 else ""
            
            if len(principal_parts)==4:
                principal_name = principal_parts[2]+'/'+principal_parts[3]
            elif len(principal_parts)==3:
                principal_name = principal_parts[2]
            else:
                principal_name = principal_parts[1] if len(principal_parts) > 1 else ""
            
            results.append([account_id, glue_aws_region, 'analysis', analysis['Name'], 
                          analysis['AnalysisId'], ptype, principal_name, arn, additional_info, actions])
        return results
    except Exception as e:
        print(f"Error processing analysis {analysis['AnalysisId']}: {e}")
        return []

def process_theme_permissions(theme):
    """Process permissions for a single theme"""
    if theme['ThemeId'] in ['SEASIDE', 'CLASSIC', 'MIDNIGHT', 'RAINIER', 'AQUASCAPE']:
        return []
    
    try:
        response = call_with_backoff(lambda: describe_theme_permissions(account_id, theme['ThemeId'], glue_aws_region))
        permissions = response['Permissions']
        results = []
        
        for principal in permissions:
            actions = '|'.join(principal['Actions'])
            arn = principal['Principal']
            principal_parts = principal['Principal'].split("/")
            ptype = principal_parts[0].split(":")[-1]
            additional_info = principal_parts[-2] if len(principal_parts) > 2 else ""
            
            if len(principal_parts)==4:
                principal_name = principal_parts[2]+'/'+principal_parts[3]
            elif len(principal_parts)==3:
                principal_name = principal_parts[2]
            else:
                principal_name = principal_parts[1] if len(principal_parts) > 1 else ""
            
            results.append([account_id, glue_aws_region, 'theme', theme['Name'], 
                          theme['ThemeId'], ptype, principal_name, arn, additional_info, actions])
        return results
    except Exception as e:
        print(f"Error processing theme {theme['ThemeId']}: {e}")
        return []

def process_user_groups(user_data):
    """Process group memberships for a single user"""
    account_id, ns, user = user_data
    results = []
    
    if user['UserName'] == 'N/A':
        return results
    
    try:
        groups = list_user_groups(user['UserName'], account_id, aws_region, ns)
        if len(groups) == 0:
            results.append([account_id, ns, None, user['UserName'], user['Email'], user['Role'], user['IdentityType'], user['Arn']])
        else:
            for group in groups:
                results.append([account_id, ns, group['GroupName'], user['UserName'], user['Email'], user['Role'], user['IdentityType'], user['Arn']])
    except Exception as e:
        print(f"Error processing user {user['UserName']}: {e}")
    
    return results

def process_users_parallel(user_list, csv_path, batch_size=30, max_workers=2):
    """Process users in parallel and write incrementally"""
    csv_lock = threading.Lock()
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        for i in range(0, len(user_list), batch_size):
            batch = user_list[i:i+batch_size]
            print(f"Processing user batch {i//batch_size + 1}/{(len(user_list)-1)//batch_size + 1}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(process_user_groups, user_data): user_data for user_data in batch}
                
                for future in as_completed(futures):
                    try:
                        results = future.result()
                        if results:
                            with csv_lock:
                                for row in results:
                                    writer.writerow(row)
                    except Exception as e:
                        print(f"Error in user parallel processing: {e}")
            
            # Small delay between batches
            time.sleep(1)

def process_assets_parallel(assets, process_func, batch_size=20, max_workers=2):
    """Process assets in parallel batches and write incrementally"""
    csv_lock = threading.Lock()
    
    with open(path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        for i in range(0, len(assets), batch_size):
            batch = assets[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(assets)-1)//batch_size + 1}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(process_func, asset): asset for asset in batch}
                
                for future in as_completed(futures):
                    try:
                        results = future.result()
                        if results:
                            with csv_lock:
                                for row in results:
                                    writer.writerow(row)
                    except Exception as e:
                        print(f"Error in parallel processing: {e}")
            
            # Add delay between batches to avoid throttling
            time.sleep(2)

if __name__ == "__main__":
    sts_client = boto3.client("sts", region_name=aws_region, config=default_botocore_config())
    account_id = sts_client.get_caller_identity()["Account"]

    # call s3 bucket
    s3 = boto3.resource('s3')
    bucketname = s3_output_path.replace('s3://', '').split('/')[0]
    bucket = s3.Bucket(bucketname)

    s3_prefix = '/'.join(s3_output_path.replace('s3://', '').split('/')[1:])
    key = f'{s3_prefix}/group_membership/group_membership.csv'
    key2 = f'{s3_prefix}/object_access/object_access.csv'
    tmpdir = tempfile.mkdtemp()
    local_file_name = 'group_membership.csv'
    local_file_name2 = 'object_access.csv'
    path = os.path.join(tmpdir, local_file_name)

    lists = []
    user_data_list = []
    namespaces = list_namespaces(account_id, aws_region)
    
    # Collect all users from all namespaces first
    for ns in namespaces:
        try:
            ns_name = ns['Name']
            users = list_users(account_id, aws_region, ns_name)
            
            for user in users:
                user_data_list.append((account_id, ns_name, user))
                
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"Account " + account_id + " is not signed up with QuickSight with namespace " + ns_name + " . Skipping this namespace.")
                continue
        except Exception as e:
            print(e)
            continue
    
    print(f"Total users to process: {len(user_data_list)}")
    
    # Process users in parallel
    try:
        process_users_parallel(user_data_list, path)
        print(f"User processing completed. File size: {os.path.getsize(path)} bytes")
        bucket.upload_file(path, key)
        print(f"Group membership CSV uploaded to {key}")
    except Exception as e:
        print(f"Error in user processing: {e}")
        raise

    path = os.path.join(tmpdir, local_file_name2)
    print(f"Starting asset processing. Second CSV path: {path}")
    
    # Create empty CSV file first
    with open(path, 'w', newline='') as csvfile:
        pass
    
    try:
        # Process all asset types in parallel with reduced concurrency
        print("Processing dashboards...")
        dashboards = list_dashboards(account_id, glue_aws_region)
        print(f"Found {len(dashboards)} dashboards")
        process_assets_parallel(dashboards, process_dashboard_permissions)
        
        print("Processing datasets...")
        datasets = list_datasets(account_id, glue_aws_region)
        print(f"Found {len(datasets)} datasets")
        process_assets_parallel(datasets, process_dataset_permissions)
        
        print("Processing datasources...")
        datasources = list_datasources(account_id, glue_aws_region)
        print(f"Found {len(datasources)} datasources")
        process_assets_parallel(datasources, process_datasource_permissions)
        
        print("Processing analyses...")
        analyses = list_analyses(account_id, glue_aws_region)
        print(f"Found {len(analyses)} analyses")
        process_assets_parallel(analyses, process_analysis_permissions)
        
        print("Processing themes...")
        themes = list_themes(account_id, glue_aws_region)
        print(f"Found {len(themes)} themes")
        process_assets_parallel(themes, process_theme_permissions)
        
        print(f"Asset processing completed. File size: {os.path.getsize(path)} bytes")
        
        # upload file from tmp to s3 key
        bucket.upload_file(path, key2)
        print(f"Object access CSV uploaded to {key2}")
        
    except Exception as e:
        print(f"Error in asset processing: {e}")
        raise
    
    # Commit the job
    job.commit()


