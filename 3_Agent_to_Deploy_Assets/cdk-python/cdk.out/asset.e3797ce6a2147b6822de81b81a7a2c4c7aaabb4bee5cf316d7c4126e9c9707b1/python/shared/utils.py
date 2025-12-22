import boto3
import botocore
import os
from typing import Dict, Union, Optional

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
        user_agent_extra="qs_sdk_biops",
    )

def assume_role(aws_account_number: str, role_name: str, aws_region: str):
    """Assume IAM role and return session."""
    sts_client = boto3.client('sts', config=default_botocore_config())
    response = sts_client.assume_role(
        RoleArn=f'arn:aws:iam::{aws_account_number}:role/{role_name}',
        RoleSessionName='quicksight-lambda'
    )
    
    return boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken'],
        region_name=aws_region
    )

def get_user_arn(session, username: str, region: str = 'us-east-1', namespace: str = 'default'):
    """Get user ARN for QuickSight permissions."""
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    
    if username == 'root':
        return f'arn:aws:iam::{account_id}:{username}'
    else:
        return f"arn:aws:quicksight:{region}:{account_id}:user/{namespace}/{username}"