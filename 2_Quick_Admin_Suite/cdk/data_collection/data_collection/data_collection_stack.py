from aws_cdk import Stack
import aws_cdk as cdk
import aws_cdk.aws_glue as glue
import aws_cdk.aws_iam as iam
import aws_cdk.aws_s3 as s3
from constructs import Construct

class DataCollectionStack(Stack):
  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Resources
    quickSightAdminConsole2025 = iam.CfnRole(self, 'QuickSightAdminConsole2025',
          role_name = 'QuickSightAdminConsole2025',
          assume_role_policy_document = {
            'Version': '2012-10-17',
            'Statement': [
              {
                'Effect': 'Allow',
                'Principal': {
                  'Service': [
                    'glue.amazonaws.com',
                    'cloudformation.amazonaws.com',
                  ],
                },
                'Action': [
                  'sts:AssumeRole',
                ],
              },
            ],
          },
          policies = [
            {
              'policyName': 'QuickSight-AdminConsole-2025',
              'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [
                  {
                    'Action': [
                      'iam:*',
                      'quicksight:*',
                      'glue:*',
                      's3:*',
                      'sts:AssumeRole',
                      'cloudwatch:*',
                      'logs:*',
                    ],
                    'Resource': '*',
                    'Effect': 'Allow',
                  },
                ],
              },
            },
          ],
        )
    quickSightAdminConsole2025.cfn_options.metadata = {
      'AWS::CloudFormation::Designer': {
        'id': '137f8de2-0d45-4490-a6a7-04356c185c4a',
      },
    }

    adminconsoledatasetdashboardinfoschedule = glue.CfnTrigger(self, 'adminconsoledatasetdashboardinfoschedule',
          type = 'SCHEDULED',
          description = 'Glue Trigger to run adminconsoledatasetdashboardinfo glue job every 3 hours',
          schedule = 'cron(0 */3 * * ? *)',
          actions = [
            {
              'jobName': 'adminconsoledatasetdashboardinfo',
            },
          ],
          name = 'adminconsoledatasetdashboardinfo-every-3-hour',
          start_on_creation = True,
        )

    adminconsolenew = s3.CfnBucket(self, 'adminconsolenew',
          access_control = 'Private',
          public_access_block_configuration = {
            'blockPublicAcls': True,
            'blockPublicPolicy': True,
            'ignorePublicAcls': True,
            'restrictPublicBuckets': True,
          },
          bucket_name = ''.join([
            'admin-console-new-',
            self.account,
          ]),
        )
    adminconsolenew.cfn_options.metadata = {
      'AWS::CloudFormation::Designer': {
        'id': '494a8dba-26e5-4efa-93ea-d49a84c99390',
      },
    }

    adminconsoleqobjectaccessinfoschedule = glue.CfnTrigger(self, 'adminconsoleqobjectaccessinfoschedule',
          type = 'SCHEDULED',
          description = 'Glue Trigger to run adminconsoleqobjectaccessinfo glue job every 3 hours',
          schedule = 'cron(0 */3 * * ? *)',
          actions = [
            {
              'jobName': 'adminconsoleqobjectaccessinfo',
            },
          ],
          name = 'adminconsoleqobjectaccessinfo-every-3-hour',
          start_on_creation = True,
        )

    adminconsoleqtopicinfoschedule = glue.CfnTrigger(self, 'adminconsoleqtopicinfoschedule',
          type = 'SCHEDULED',
          description = 'Glue Trigger to run adminconsoleqtopicinfo glue job every 3 hours',
          schedule = 'cron(0 */3 * * ? *)',
          actions = [
            {
              'jobName': 'adminconsoleqtopicinfo',
            },
          ],
          name = 'adminconsoleqtopicinfo-every-3-hour',
          start_on_creation = True,
        )

    adminconsoleuserdataaccessinfoschedule = glue.CfnTrigger(self, 'adminconsoleuserdataaccessinfoschedule',
          type = 'SCHEDULED',
          description = 'Glue Trigger to run adminconsoleuserdataaccessinfo glue job every 3 hours',
          schedule = 'cron(0 */3 * * ? *)',
          actions = [
            {
              'jobName': 'adminconsoleuserdataaccessinfo',
            },
          ],
          name = 'adminconsoleuserdataaccessinfo-every-3-hour',
          start_on_creation = True,
        )

    folderassetsglueschedule = glue.CfnTrigger(self, 'folderassetsglueschedule',
          type = 'SCHEDULED',
          description = 'Glue Trigger to run folderassetsglue job every 3 hours',
          schedule = 'cron(0 */3 * * ? *)',
          actions = [
            {
              'jobName': 'folderassetsglue',
            },
          ],
          name = 'folderassetsglue-every-3-hour',
          start_on_creation = True,
        )

    adminconsoledatasetdashboardinfo = glue.CfnJob(self, 'adminconsoledatasetdashboardinfo',
          command = {
            'name': 'pythonshell',
            'pythonVersion': '3.9',
            'scriptLocation': f"""s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoledatasetdashboardinfo.py""",
          },
          default_arguments = {
            '--AWS_REGION': f"""{self.region}""",
          },
          glue_version = '3.0',
          execution_property = {
            'maxConcurrentRuns': 1,
          },
          max_capacity = 1,
          max_retries = 0,
          name = 'adminconsoledatasetdashboardinfo',
          role = quickSightAdminConsole2025.attr_arn,
          timeout = 120,
        )
    adminconsoledatasetdashboardinfo.cfn_options.metadata = {
      'AWS::CloudFormation::Designer': {
        'id': 'c4462e36-ef27-43d6-a0df-01246a77b117',
      },
    }
    adminconsoledatasetdashboardinfo.add_dependency(adminconsolenew)

    adminconsoleqobjectaccessinfo = glue.CfnJob(self, 'adminconsoleqobjectaccessinfo',
          command = {
            'name': 'glueetl',
            'pythonVersion': '3',
            'scriptLocation': f"""s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoleqobjectaccessinfo.py""",
          },
          default_arguments = {
            '--region': f"""{self.region}""",
            '--aws_account_id': f"""{self.account}""",
            '--output_s3_path': f"""s3://admin-console-new-{self.account}/monitoring/quicksight/q_object_access""",
          },
          glue_version = '5.0',
          execution_property = {
            'maxConcurrentRuns': 1,
          },
          max_retries = 0,
          name = 'adminconsoleqobjectaccessinfo',
          role = quickSightAdminConsole2025.attr_arn,
          timeout = 120,
          worker_type = 'G.1X',
          number_of_workers = 2,
        )
    adminconsoleqobjectaccessinfo.add_dependency(adminconsolenew)

    adminconsoleqtopicinfo = glue.CfnJob(self, 'adminconsoleqtopicinfo',
          command = {
            'name': 'glueetl',
            'pythonVersion': '3',
            'scriptLocation': f"""s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoleqtopicinfo.py""",
          },
          default_arguments = {
            '--AWS_REGION': f"""{self.region}""",
            '--AWS_ACCOUNT_ID': f"""{self.account}""",
            '--S3_OUTPUT_PATH': f"""s3://admin-console-new-{self.account}/monitoring/quicksight/q_topics_info""",
          },
          glue_version = '5.0',
          execution_property = {
            'maxConcurrentRuns': 1,
          },
          max_retries = 0,
          name = 'adminconsoleqtopicinfo',
          role = quickSightAdminConsole2025.attr_arn,
          timeout = 120,
          worker_type = 'G.1X',
          number_of_workers = 2,
        )
    adminconsoleqtopicinfo.add_dependency(adminconsolenew)

    adminconsoleuserdataaccessinfo = glue.CfnJob(self, 'adminconsoleuserdataaccessinfo',
          command = {
            'name': 'pythonshell',
            'pythonVersion': '3.9',
            'scriptLocation': f"""s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoleuserdataaccessinfo.py""",
          },
          default_arguments = {
            '--AWS_REGION': f"""{self.region}""",
          },
          glue_version = '3.0',
          execution_property = {
            'maxConcurrentRuns': 1,
          },
          max_capacity = 1,
          max_retries = 0,
          name = 'adminconsoleuserdataaccessinfo',
          role = quickSightAdminConsole2025.attr_arn,
          timeout = 120,
        )
    adminconsoleuserdataaccessinfo.cfn_options.metadata = {
      'AWS::CloudFormation::Designer': {
        'id': 'c4462e36-ef27-43d6-a0df-01246a77b117',
      },
    }
    adminconsoleuserdataaccessinfo.add_dependency(adminconsolenew)

    folderassetsglue = glue.CfnJob(self, 'folderassetsglue',
          command = {
            'name': 'pythonshell',
            'pythonVersion': '3.9',
            'scriptLocation': 's3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsolefolderinfo.py',
          },
          default_arguments = {
            '--AWS_REGION': f"""{self.region}""",
          },
          glue_version = '3.0',
          execution_property = {
            'maxConcurrentRuns': 1,
          },
          max_capacity = 1,
          max_retries = 0,
          name = 'folderassetsglue',
          role = quickSightAdminConsole2025.attr_arn,
          timeout = 120,
        )
    folderassetsglue.add_dependency(adminconsolenew)

    # Outputs
    """
      The s3 location of group_membership.csv for you to utilize in next Athena tables creation stack
    """
    self.groupmembership = f"""s3://admin-console-new-{self.account}/monitoring/quicksight/group_membership"""
    cdk.CfnOutput(self, 'CfnOutputgroupmembership', 
      key = 'groupmembership',
      description = 'The s3 location of group_membership.csv for you to utilize in next Athena tables creation stack',
      value = str(self.groupmembership),
    )

    """
      The s3 location of object_access.csv for you to utilize in next Athena tables creation stack
    """
    self.objectaccess = f"""s3://admin-console-new-{self.account}/monitoring/quicksight/object_access"""
    cdk.CfnOutput(self, 'CfnOutputobjectaccess', 
      key = 'objectaccess',
      description = 'The s3 location of object_access.csv for you to utilize in next Athena tables creation stack',
      value = str(self.objectaccess),
    )

    """
      The s3 location of folder_assets.csv for you to utilize in next Athena tables creation stack
    """
    self.folderassets = f"""s3://admin-console-new-{self.account}/monitoring/quicksight/folder_assets/folder_assets.csv"""
    cdk.CfnOutput(self, 'CfnOutputfolderassets', 
      key = 'folderassets',
      description = 'The s3 location of folder_assets.csv for you to utilize in next Athena tables creation stack',
      value = str(self.folderassets),
    )

    """
      The s3 location of folder_lk.csv for you to utilize in next Athena tables creation stack
    """
    self.folderlk = f"""s3://admin-console-new-{self.account}/monitoring/quicksight/folder_lk/folder_lk.csv"""
    cdk.CfnOutput(self, 'CfnOutputfolderlk', 
      key = 'folderlk',
      description = 'The s3 location of folder_lk.csv for you to utilize in next Athena tables creation stack',
      value = str(self.folderlk),
    )

    """
      The s3 location of folder_path.csv for you to utilize in next Athena tables creation stack
    """
    self.folderpath = f"""s3://admin-console-new-{self.account}/monitoring/quicksight/folder_path/folder_path.csv"""
    cdk.CfnOutput(self, 'CfnOutputfolderpath', 
      key = 'folderpath',
      description = 'The s3 location of folder_path.csv for you to utilize in next Athena tables creation stack',
      value = str(self.folderpath),
    )

    """
      The table name of cloudtrail log for you to utilize in next Athena tables creation stack
    """
    self.cloudtraillogtablename = 'cloudtrail_logs'
    cdk.CfnOutput(self, 'CfnOutputcloudtraillogtablename', 
      key = 'cloudtraillogtablename',
      description = 'The table name of cloudtrail log for you to utilize in next Athena tables creation stack',
      value = str(self.cloudtraillogtablename),
    )

    """
      The s3 location of cloudtrail log for you to utilize in next Athena tables creation stack
    """
    self.cloudtraillog = f"""s3://cloudtrail-awslogs-{self.account}-do-not-delete/AWSLogs/{self.account}/CloudTrail"""
    cdk.CfnOutput(self, 'CfnOutputcloudtraillog', 
      key = 'cloudtraillog',
      description = 'The s3 location of cloudtrail log for you to utilize in next Athena tables creation stack',
      value = str(self.cloudtraillog),
    )



