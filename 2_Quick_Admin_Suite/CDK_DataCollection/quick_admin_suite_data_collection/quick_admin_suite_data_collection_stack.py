from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_glue as glue,
    aws_s3 as s3,
    aws_kinesisfirehose as firehose,
    aws_cloudwatch as cloudwatch,
    CfnOutput,
    CfnParameter,
    RemovalPolicy
)
from constructs import Construct

class QuickAdminSuiteDataCollectionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Parameters
        script_bucket_name = CfnParameter(
            self, "ScriptBucketName",
            type="String",
            default="admin-console-cfn-dataprepare-code",
            description="S3 bucket name containing Glue job scripts"
        )

        # IAM Role
        quicksight_admin_role = iam.Role(
            self, "QuickSuiteAdmin",
            role_name=f"QuickSuiteAdmin-{self.account}",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("glue.amazonaws.com"),
                iam.ServicePrincipal("cloudformation.amazonaws.com"),
                iam.ServicePrincipal("firehose.amazonaws.com"),
                iam.ServicePrincipal("streams.metrics.cloudwatch.amazonaws.com")
            ),
            inline_policies={
                f"Quick-Suite-Admin-{self.account}": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "iam:Get*",
                                "iam:List*",
                                "iam:Create*",
                                "iam:Update*",
                                "iam:PassRole",
                                "quicksight:*",
                                "glue:*",
                                "s3:*",
                                "sts:AssumeRole",
                                "cloudwatch:*",
                                "logs:*",
                                "firehose:PutRecord",
                                "firehose:PutRecordBatch"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        # Main S3 Bucket (consolidated)
        admin_suite_bucket = s3.Bucket(
            self, "adminsuites3",
            bucket_name=f"admin-suite-{self.account}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN
        )

        # Glue Jobs
        self._create_glue_jobs(quicksight_admin_role, admin_suite_bucket, script_bucket_name)

        # CloudWatch Metric Streams
        self._create_metric_streams(quicksight_admin_role, admin_suite_bucket)

        # Outputs
        self._create_outputs(admin_suite_bucket)

    def _create_glue_jobs(self, role: iam.Role, bucket: s3.Bucket, script_bucket_name: CfnParameter):
        # Assets Access Job
        assets_access_job = glue.CfnJob(
            self, "etljobadminsuiteassetsaccess",
            name="admin_suite_user_info_access_manage",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{script_bucket_name.value_as_string}/glue/scripts/2025/admin_suite_user_info_access_manage.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region,
                "--S3_OUTPUT_PATH": f"s3://admin-suite-{self.account}/monitoring/quicksight/assets_access"
            },
            glue_version="5.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_retries=0,
            timeout=120,
            worker_type="G.1X",
            number_of_workers=2
        )
        assets_access_job.add_depends_on(bucket.node.default_child)

        # Assets Metadata Job
        assets_metadata_job = glue.CfnJob(
            self, "etljobadminsuiteassetsmetadata",
            name="admin_suite_dataset",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{script_bucket_name.value_as_string}/glue/scripts/2025/admin_suite_dataset.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region,
                "--S3_OUTPUT_PATH": f"s3://admin-suite-{self.account}/monitoring/quicksight/dataset"
            },
            glue_version="5.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_retries=0,
            timeout=120,
            worker_type="G.1X",
            number_of_workers=2
        )
        assets_metadata_job.add_depends_on(bucket.node.default_child)

        # Folder Assets Job
        folder_assets_job = glue.CfnJob(
            self, "etljobadminsuitefolderassets",
            name="admin_suite_folder",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{script_bucket_name.value_as_string}/glue/scripts/2025/admin_suite_folder.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region,
                "--S3_OUTPUT_PATH": f"s3://admin-suite-{self.account}/monitoring/quicksight/folder_assets"
            },
            glue_version="5.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_retries=0,
            timeout=120,
            worker_type="G.1X",
            number_of_workers=2
        )
        folder_assets_job.add_depends_on(bucket.node.default_child)

        # Q Metadata Job
        q_metadata_job = glue.CfnJob(
            self, "etljobadminsuiteqmetadata",
            name="admin_suite_q",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{script_bucket_name.value_as_string}/glue/scripts/2025/admin_suite_q.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region,
                "--AWS_ACCOUNT_ID": self.account,
                "--S3_OUTPUT_PATH": f"s3://admin-suite-{self.account}/monitoring/quicksight/q_md"
            },
            glue_version="5.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_retries=0,
            timeout=120,
            worker_type="G.1X",
            number_of_workers=2
        )
        q_metadata_job.add_depends_on(bucket.node.default_child)

        # Datasource Properties Job
        datasource_properties_job = glue.CfnJob(
            self, "etljobadminsuitedatasourceproperties",
            name="admin_suite_datasource",
            role=role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{script_bucket_name.value_as_string}/glue/scripts/2025/admin_suite_datasource.py"
            ),
            default_arguments={
                "--AWS_REGION": self.region,
                "--QUICKSIGHT_IDENTITY_REGION": self.region,
                "--S3_OUTPUT_PATH": f"s3://admin-suite-{self.account}/monitoring/quicksight/datasource_property"
            },
            glue_version="5.0",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(max_concurrent_runs=1),
            max_retries=0,
            timeout=120,
            worker_type="G.1X",
            number_of_workers=2
        )
        datasource_properties_job.add_depends_on(bucket.node.default_child)

        # Glue Triggers (Schedules)
        self._create_glue_triggers()

    def _create_glue_triggers(self):
        # Assets Access Schedule
        glue.CfnTrigger(
            self, "etljobadminsuiteassetsaccessschedule",
            name="etl-job-admin-suite-assets-access-daily",
            type="SCHEDULED",
            description="Glue Trigger to run admin_suite_user_info_access_manage glue job daily",
            schedule="cron(0 2 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="admin_suite_user_info_access_manage")],
            start_on_creation=True
        )

        # Assets Metadata Schedule
        glue.CfnTrigger(
            self, "etljobadminsuiteassetsmetadataschedule",
            name="etl-job-admin-suite-assets-metadata-daily",
            type="SCHEDULED",
            description="Glue Trigger to run admin_suite_dataset glue job daily",
            schedule="cron(15 2 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="admin_suite_dataset")],
            start_on_creation=True
        )

        # Folder Assets Schedule
        glue.CfnTrigger(
            self, "etljobadminsuitefolderassetsschedule",
            name="etl-job-admin-suite-folder-assets-daily",
            type="SCHEDULED",
            description="Glue Trigger to run admin_suite_folder job daily",
            schedule="cron(30 2 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="admin_suite_folder")],
            start_on_creation=True
        )

        # Q Metadata Schedule
        glue.CfnTrigger(
            self, "etljobadminsuiteqmetadataschedule",
            name="etl-job-admin-suite-q-metadata-daily",
            type="SCHEDULED",
            description="Glue Trigger to run admin_suite_q glue job daily",
            schedule="cron(45 2 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="admin_suite_q")],
            start_on_creation=True
        )

        # Datasource Properties Schedule
        glue.CfnTrigger(
            self, "etljobadminsuitedatasourcepropertieschedule",
            name="etl-job-admin-suite-datasource-properties-daily",
            type="SCHEDULED",
            description="Glue Trigger to run admin_suite_datasource glue job daily",
            schedule="cron(5 3 * * ? *)",
            actions=[glue.CfnTrigger.ActionProperty(job_name="admin_suite_datasource")],
            start_on_creation=True
        )

    def _create_metric_streams(self, role: iam.Role, bucket: s3.Bucket):
        # Firehose Delivery Streams
        ds_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsds",
            delivery_stream_name=f"MetricStreams-cw-qs-ds-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=bucket.bucket_arn,
                prefix="cloudwatch/cw-qs-ds/",
                role_arn=role.role_arn
            )
        )
        ds_firehose.add_depends_on(role.node.default_child)

        dash_visual_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsdashvisual",
            delivery_stream_name=f"MetricStreams-cw-qs-dash-visual-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=bucket.bucket_arn,
                prefix="cloudwatch/cw-qs-dash-visual/",
                role_arn=role.role_arn
            )
        )
        dash_visual_firehose.add_depends_on(role.node.default_child)

        spice_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsspice",
            delivery_stream_name=f"MetricStreams-cw-qs-spice-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=bucket.bucket_arn,
                prefix="cloudwatch/cw-qs-spice/",
                role_arn=role.role_arn
            )
        )
        spice_firehose.add_depends_on(role.node.default_child)

        qindex_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsqindex",
            delivery_stream_name=f"MetricStreams-cw-qs-qindex-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=bucket.bucket_arn,
                prefix="cloudwatch/cw-qs-qindex/",
                role_arn=role.role_arn
            )
        )
        qindex_firehose.add_depends_on(role.node.default_child)

        qaction_firehose = firehose.CfnDeliveryStream(
            self, "FirehoseDeliveryStreamcwqsqaction",
            delivery_stream_name=f"MetricStreams-cw-qs-qaction-{self.account}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=bucket.bucket_arn,
                prefix="cloudwatch/cw-qs-qaction/",
                role_arn=role.role_arn
            )
        )
        qaction_firehose.add_depends_on(role.node.default_child)

        # CloudWatch Metric Streams
        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamDS",
            name="cw-qs-ds",
            firehose_arn=ds_firehose.attr_arn,
            role_arn=role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight",
                    metric_names=["IngestionRowCount", "IngestionLatency", "IngestionInvocationCount", "IngestionErrorCount"]
                )
            ]
        )

        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamDashVisual",
            name="cw-qs-dash-visual",
            firehose_arn=dash_visual_firehose.attr_arn,
            role_arn=role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight",
                    metric_names=["VisualLoadTime", "DashboardViewLoadTime", "DashboardViewCount", "VisualLoadErrorCount"]
                )
            ]
        )

        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamSPICE",
            name="cw-qs-spice",
            firehose_arn=spice_firehose.attr_arn,
            role_arn=role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight",
                    metric_names=["SPICECapacityLimitInMB", "SPICECapacityConsumedInMB"]
                )
            ]
        )

        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamQIndex",
            name="cw-qs-qindex",
            firehose_arn=qindex_firehose.attr_arn,
            role_arn=role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight",
                    metric_names=["QuickIndexDocumentCount", "QuickIndexExtractedTextSize"]
                )
            ]
        )

        cloudwatch.CfnMetricStream(
            self, "CloudWatchMetricStreamQAction",
            name="cw-qs-qaction",
            firehose_arn=qaction_firehose.attr_arn,
            role_arn=role.role_arn,
            output_format="json",
            include_filters=[
                cloudwatch.CfnMetricStream.MetricStreamFilterProperty(
                    namespace="AWS/QuickSight",
                    metric_names=["ActionInvocationError", "ActionInvocationCount"]
                )
            ]
        )

    def _create_outputs(self, bucket: s3.Bucket):
        CfnOutput(
            self, "groupmembership",
            description="The s3 location of group_membership.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-suite-{self.account}/monitoring/quicksight/group_membership"
        )

        CfnOutput(
            self, "objectaccess",
            description="The s3 location of object_access.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-suite-{self.account}/monitoring/quicksight/object_access"
        )

        CfnOutput(
            self, "folderassets",
            description="The s3 location of folder_assets.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-suite-{self.account}/monitoring/quicksight/folder_assets/folder_assets.csv"
        )

        CfnOutput(
            self, "folderlk",
            description="The s3 location of folder_lk.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-suite-{self.account}/monitoring/quicksight/folder_lk/folder_lk.csv"
        )

        CfnOutput(
            self, "folderpath",
            description="The s3 location of folder_path.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-suite-{self.account}/monitoring/quicksight/folder_path/folder_path.csv"
        )

        CfnOutput(
            self, "datasetsproperties",
            description="The s3 location of datasets_properties.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-suite-{self.account}/monitoring/quicksight/datasets_properties/datasets_properties.csv"
        )

        CfnOutput(
            self, "datasourceproperty",
            description="The s3 location of datasource_property.csv for you to utilize in next Athena tables creation stack",
            value=f"s3://admin-suite-{self.account}/monitoring/quicksight/datasource_property/datasource_property.csv"
        )