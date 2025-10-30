from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_glue as glue,
    aws_s3 as s3,
    aws_kinesisfirehose as firehose,
    aws_cloudwatch as cloudwatch,
    aws_events as events,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct

class QuickAdminSuiteDataCollectionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # IAM Role
        quicksight_admin_role = iam.Role(
            self, "QuickSightAdminConsole2025",
            role_name="QuickSightAdminConsole2025",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("glue.amazonaws.com"),
                iam.ServicePrincipal("cloudformation.amazonaws.com"),
                iam.ServicePrincipal("firehose.amazonaws.com")
            ),
            inline_policies={
                "QuickSight-AdminConsole-2025": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "iam:*",
                                "quicksight:*",
                                "glue:*",
                                "s3:*",
                                "sts:AssumeRole",
                                "cloudwatch:*",
                                "logs:*"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        # Main S3 Bucket
        admin_console_bucket = s3.Bucket(
            self, "adminconsolenew",
            bucket_name=f"admin-console-new-{self.account}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN
        )

        # CloudWatch Metrics S3 Buckets
        cw_dash_visual_bucket = s3.Bucket(
            self, "S3BucketMetricstreamscwqsdashvisual",
            bucket_name=f"cw-qs-dash-visual-{self.account}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN
        )

        cw_ds_bucket = s3.Bucket(
            self, "S3BucketMetricstreamscwqsds",
            bucket_name=f"cw-qs-ds-{self.account}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN
        )

        cw_spice_bucket = s3.Bucket(
            self, "S3BucketMetricstreamscwqsspice",
            bucket_name=f"cw-qs-spice-{self.account}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN
        )

        cw_qindex_bucket = s3.Bucket(
            self, "S3BucketMetricstreamscwqsqindex",
            bucket_name=f"cw-qs-qindex-{self.account}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN
        )

        cw_qaction_bucket = s3.Bucket(
            self, "S3BucketMetricstreamscwqsqaction",
            bucket_name=f"cw-qs-qaction-{self.account}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN
        )

        # Glue Jobs
        self._create_glue_jobs(quicksight_admin_role, admin_console_bucket)

        # CloudWatch Metric Streams
        self._create_metric_streams(quicksight_admin_role, cw_ds_bucket, cw_dash_visual_bucket, 
                                  cw_spice_bucket, cw_qindex_bucket, cw_qaction_bucket)

        # Outputs
        self._create_outputs(admin_console_bucket)

    def _create_glue_jobs(self, role: iam.Role, bucket: s3.Bucket):
        # Assets Access Job
        assets_access_job = glue.CfnJob(
            self, "etljobadminsuiteassetsaccess",
            name="etl_job_admin_suite_assets_access",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                python_version="3.9",
                script_location=f"s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoleuserdataaccessinfo.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region
            },
            glue_version="3.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_capacity=1,
            max_retries=0,
            timeout=120
        )
        assets_access_job.add_depends_on(bucket.node.default_child)

        # Assets Metadata Job
        assets_metadata_job = glue.CfnJob(
            self, "etljobadminsuiteassetsmetadata",
            name="etl_job_admin_suite_assets_metadata",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                python_version="3.9",
                script_location=f"s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoledatasetdashboardinfo.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region
            },
            glue_version="3.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_capacity=1,
            max_retries=0,
            timeout=120
        )
        assets_metadata_job.add_depends_on(bucket.node.default_child)

        # Folder Assets Job
        folder_assets_job = glue.CfnJob(
            self, "etljobadminsuitefolderassets",
            name="etl_job_admin_suite_folder_assets",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                python_version="3.9",
                script_location="s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsolefolderinfo.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region
            },
            glue_version="3.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_capacity=1,
            max_retries=0,
            timeout=120
        )
        folder_assets_job.add_depends_on(bucket.node.default_child)

        # Q Access Job
        q_access_job = glue.CfnJob(
            self, "etljobadminsuiteqaccess",
            name="etl_job_admin_suite_q_access",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoleqobjectaccessinfo.py"
            ),
            default_arguments={
                "--region": self.region,
                "--aws_account_id": self.account,
                "--output_s3_path": f"s3://admin-console-new-{self.account}/monitoring/quicksight/q_object_access"
            },
            glue_version="5.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_retries=0,
            timeout=120,
            worker_type="G.1X",
            number_of_workers=2
        )
        q_access_job.add_depends_on(bucket.node.default_child)

        # Q Metadata Job
        q_metadata_job = glue.CfnJob(
            self, "etljobadminsuiteqmetadata",
            name="etl_job_admin_suite_q_metadata",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/adminconsoleqtopicinfo.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region,
                "--AWS_ACCOUNT_ID": self.account,
                "--S3_OUTPUT_PATH": f"s3://admin-console-new-{self.account}/monitoring/quicksight/q_topics_info"
            },
            glue_version="5.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_retries=0,
            timeout=120,
            worker_type="G.1X",
            number_of_workers=2
        )
        q_metadata_job.add_depends_on(bucket.node.default_child)

        # DS Properties Job
        ds_properties_job = glue.CfnJob(
            self, "etljobadminsuitedsproperties",
            name="etl_job_admin_suite_ds_properties",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                python_version="3.9",
                script_location=f"s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/admin_suite_ds_property.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region
            },
            glue_version="3.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_capacity=1,
            max_retries=0,
            timeout=120
        )
        ds_properties_job.add_depends_on(bucket.node.default_child)

        # Datasource Properties Job
        datasource_properties_job = glue.CfnJob(
            self, "etljobadminsuitedatasourceproperties",
            name="etl_job_admin_suite_datasource_properties",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                python_version="3.9",
                script_location=f"s3://admin-console-cfn-dataprepare-code/glue/scripts/2025/admin_suite_datasource_property.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region,
                "--QUICKSIGHT_IDENTITY_REGION": self.region
            },
            glue_version="3.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_capacity=1,
            max_retries=0,
            timeout=120
        )
        datasource_properties_job.add_depends_on(bucket.node.default_child)

        # Glue Triggers (Schedules)
        self._create_glue_triggers()

    def _create_glue_triggers(self):
        # Assets Access Schedule
        glue.CfnTrigger(
            self, "etljobadminsuiteassetsaccessschedule",
            name="etl-job-admin-suite-assets-access-every-3-hour",
            type="SCHEDULED",
            description="Glue Trigger to run etl_job_admin_suite_assets_access glue job every 3 hours",
            schedule="cron(0 */3 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="etl_job_admin_suite_assets_access")],
            start_on_creation=True
        )

        # Assets Metadata Schedule
        glue.CfnTrigger(
            self, "etljobadminsuiteassetsmetadataschedule",
            name="etl-job-admin-suite-assets-metadata-every-3-hour",
            type="SCHEDULED",
            description="Glue Trigger to run etl_job_admin_suite_assets_metadata glue job every 3 hours",
            schedule="cron(0 */3 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="etl_job_admin_suite_assets_metadata")],
            start_on_creation=True
        )

        # Folder Assets Schedule
        glue.CfnTrigger(
            self, "etljobadminsuitefolderassetsschedule",
            name="etl-job-admin-suite-folder-assets-every-3-hour",
            type="SCHEDULED",
            description="Glue Trigger to run etl_job_admin_suite_folder_assets job every 3 hours",
            schedule="cron(0 */3 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="etl_job_admin_suite_folder_assets")],
            start_on_creation=True
        )

        # Q Metadata Schedule
        glue.CfnTrigger(
            self, "etljobadminsuiteqmetadataschedule",
            name="etl-job-admin-suite-q-metadata-every-3-hour",
            type="SCHEDULED",
            description="Glue Trigger to run etl_job_admin_suite_q_metadata glue job every 3 hours",
            schedule="cron(0 */3 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="etl_job_admin_suite_q_metadata")],
            start_on_creation=True
        )

        # Q Access Schedule
        glue.CfnTrigger(
            self, "etljobadminsuiteqaccessschedule",
            name="etl-job-admin-suite-q-access-every-3-hour",
            type="SCHEDULED",
            description="Glue Trigger to run etl_job_admin_suite_q_access glue job every 3 hours",
            schedule="cron(0 */3 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="etl_job_admin_suite_q_access")],
            start_on_creation=True
        )

        # DS Properties Schedule
        glue.CfnTrigger(
            self, "etljobadminsuitedspropertieschedule",
            name="etl-job-admin-suite-ds-properties-every-3-hour",
            type="SCHEDULED",
            description="Glue Trigger to run etl_job_admin_suite_ds_properties glue job every 3 hours",
            schedule="cron(0 */3 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="etl_job_admin_suite_ds_properties")],
            start_on_creation=True
        )

        # Datasource Properties Schedule
        glue.CfnTrigger(
            self, "etljobadminsuitedatasourcepropertieschedule",
            name="etl-job-admin-suite-datasource-properties-every-3-hour",
            type="SCHEDULED",
            description="Glue Trigger to run etl_job_admin_suite_datasource_properties glue job every 3 hours",
            schedule="cron(0 */3 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="etl_job_admin_suite_datasource_properties")],
            start_on_creation=True
        )

    def _create_metric_streams(self, role: iam.Role, ds_bucket: s3.Bucket, dash_visual_bucket: s3.Bucket,
                             spice_bucket: s3.Bucket, qindex_bucket: s3.Bucket, qaction_bucket: s3.Bucket):
        
        # CloudWatch Stream Role
        cw_stream_role = iam.Role(
            self, "QuickSuiteCWStreamRole",
            role_name="QuickSuiteCWStreamRole",
            assumed_by=iam.ServicePrincipal("streams.metrics.cloudwatch.amazonaws.com"),
            inline_policies={
                "FirehoseDeliveryPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "firehose:PutRecord",
                                "firehose:PutRecordBatch"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        # Firehose Delivery Streams
        ds_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsds",
            delivery_stream_name=f"MetricStreams-cw-qs-ds-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=ds_bucket.bucket_arn,
                role_arn=role.role_arn
            )
        )

        dash_visual_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsdashvisual",
            delivery_stream_name=f"MetricStreams-cw-qs-dash-visual-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=dash_visual_bucket.bucket_arn,
                role_arn=role.role_arn
            )
        )

        spice_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsspice",
            delivery_stream_name=f"MetricStreams-cw-qs-spice-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=spice_bucket.bucket_arn,
                role_arn=role.role_arn
            )
        )

        qindex_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsqindex",
            delivery_stream_name=f"MetricStreams-cw-qs-qindex-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=qindex_bucket.bucket_arn,
                role_arn=role.role_arn
            )
        )

        qaction_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsqaction",
            delivery_stream_name=f"MetricStreams-cw-qs-qaction-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=qaction_bucket.bucket_arn,
                role_arn=role.role_arn
            )
        )

        # CloudWatch Metric Streams
        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamDS",
            name="cw-qs-ds",
            firehose_arn=ds_firehose.attr_arn,
            role_arn=cw_stream_role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight"
                )
            ]
        )

        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamDashVisual",
            name="cw-qs-dash-visual",
            firehose_arn=dash_visual_firehose.attr_arn,
            role_arn=cw_stream_role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight"
                )
            ]
        )

        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamSPICE",
            name="cw-qs-spice",
            firehose_arn=spice_firehose.attr_arn,
            role_arn=cw_stream_role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight"
                )
            ]
        )

        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamQIndex",
            name="cw-qs-qindex",
            firehose_arn=qindex_firehose.attr_arn,
            role_arn=cw_stream_role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight"
                )
            ]
        )

        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamQAction",
            name="cw-qs-qaction",
            firehose_arn=qaction_firehose.attr_arn,
            role_arn=cw_stream_role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight"
                )
            ]
        )

    def _create_outputs(self, bucket: s3.Bucket):
        CfnOutput(
            self, "groupmembership",
            description="The s3 location of group_membership.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-console-new-{self.account}/monitoring/quicksight/group_membership"
        )

        CfnOutput(
            self, "objectaccess",
            description="The s3 location of object_access.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-console-new-{self.account}/monitoring/quicksight/object_access"
        )

        CfnOutput(
            self, "folderassets",
            description="The s3 location of folder_assets.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-console-new-{self.account}/monitoring/quicksight/folder_assets/folder_assets.csv"
        )

        CfnOutput(
            self, "folderlk",
            description="The s3 location of folder_lk.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-console-new-{self.account}/monitoring/quicksight/folder_lk/folder_lk.csv"
        )

        CfnOutput(
            self, "folderpath",
            description="The s3 location of folder_path.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-console-new-{self.account}/monitoring/quicksight/folder_path/folder_path.csv"
        )

        CfnOutput(
            self, "datasetsproperties",
            description="The s3 location of datasets_properties.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-console-new-{self.account}/monitoring/quicksight/datasets_properties/datasets_properties.csv"
        )

        CfnOutput(
            self, "datasourceproperty",
            description="The s3 location of datasource_property.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-console-new-{self.account}/monitoring/quicksight/datasource_property/datasource_property.csv"
        )