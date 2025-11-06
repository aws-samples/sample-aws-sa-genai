from aws_cdk import aws_glue as glue

def create_crawlers(stack, script_bucket_name):
    """Create Glue crawlers for CloudWatch metrics"""
    
    # Crawler for CloudWatch QuickSight Dataset
    crawler_cw_qs_ds = glue.CfnCrawler(
        stack, "CrawlerCwQsDs",
        name="crawler-cw-qs-ds",
        role=f"arn:aws:iam::{stack.account}:role/QuickSuiteAdmin-{stack.account}",
        database_name="admin-console-2025",
        targets=glue.CfnCrawler.TargetsProperty(
            s3_targets=[
                glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://admin-suite-{stack.account}/cloudwatch/cw-qs-ds/"
                )
            ]
        ),
        schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
            update_behavior="UPDATE_IN_DATABASE",
            delete_behavior="DEPRECATE_IN_DATABASE"
        ),
        configuration='{"Version": 1.0, "CrawlerOutput": {"Partitions": {"AddOrUpdateBehavior": "InheritFromTable"}, "Tables": {"AddOrUpdateBehavior": "MergeNewColumns"}}, "Grouping": {"TableGroupingPolicy": "CombineCompatibleSchemas"}, "CreatePartitionIndex": true}',
        recrawl_policy=glue.CfnCrawler.RecrawlPolicyProperty(
            recrawl_behavior="CRAWL_EVERYTHING"
        ),
        schedule=glue.CfnCrawler.ScheduleProperty(
            schedule_expression="cron(0 4 * * ? *)"
        )
    )

    # Crawler for CloudWatch QuickSight SPICE
    crawler_cw_qs_spice = glue.CfnCrawler(
        stack, "CrawlerCwQsSpice",
        name="crawler-cw-qs-spice",
        role=f"arn:aws:iam::{stack.account}:role/QuickSuiteAdmin-{stack.account}",
        database_name="admin-console-2025",
        targets=glue.CfnCrawler.TargetsProperty(
            s3_targets=[
                glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://admin-suite-{stack.account}/cloudwatch/cw-qs-spice/"
                )
            ]
        ),
        schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
            update_behavior="UPDATE_IN_DATABASE",
            delete_behavior="DEPRECATE_IN_DATABASE"
        ),
        configuration='{"Version": 1.0, "CrawlerOutput": {"Partitions": {"AddOrUpdateBehavior": "InheritFromTable"}, "Tables": {"AddOrUpdateBehavior": "MergeNewColumns"}}, "Grouping": {"TableGroupingPolicy": "CombineCompatibleSchemas"}, "CreatePartitionIndex": true}',
        recrawl_policy=glue.CfnCrawler.RecrawlPolicyProperty(
            recrawl_behavior="CRAWL_EVERYTHING"
        ),
        schedule=glue.CfnCrawler.ScheduleProperty(
            schedule_expression="cron(15 4 * * ? *)"
        )
    )

    # Crawler for CloudWatch QuickSight QIndex
    crawler_cw_qs_qindex = glue.CfnCrawler(
        stack, "CrawlerCwQsQIndex",
        name="crawler-cw-qs-qindex",
        role=f"arn:aws:iam::{stack.account}:role/QuickSuiteAdmin-{stack.account}",
        database_name="admin-console-2025",
        targets=glue.CfnCrawler.TargetsProperty(
            s3_targets=[
                glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://admin-suite-{stack.account}/cloudwatch/cw-qs-qindex/"
                )
            ]
        ),
        schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
            update_behavior="UPDATE_IN_DATABASE",
            delete_behavior="DEPRECATE_IN_DATABASE"
        ),
        configuration='{"Version": 1.0, "CrawlerOutput": {"Partitions": {"AddOrUpdateBehavior": "InheritFromTable"}, "Tables": {"AddOrUpdateBehavior": "MergeNewColumns"}}, "Grouping": {"TableGroupingPolicy": "CombineCompatibleSchemas"}, "CreatePartitionIndex": true}',
        recrawl_policy=glue.CfnCrawler.RecrawlPolicyProperty(
            recrawl_behavior="CRAWL_EVERYTHING"
        ),
        schedule=glue.CfnCrawler.ScheduleProperty(
            schedule_expression="cron(30 4 * * ? *)"
        )
    )

    # Crawler for CloudWatch QuickSight QAction
    crawler_cw_qs_qaction = glue.CfnCrawler(
        stack, "CrawlerCwQsQAction",
        name="crawler-cw-qs-qaction",
        role=f"arn:aws:iam::{stack.account}:role/QuickSuiteAdmin-{stack.account}",
        database_name="admin-console-2025",
        targets=glue.CfnCrawler.TargetsProperty(
            s3_targets=[
                glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://admin-suite-{stack.account}/cloudwatch/cw-qs-qaction/"
                )
            ]
        ),
        schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
            update_behavior="UPDATE_IN_DATABASE",
            delete_behavior="DEPRECATE_IN_DATABASE"
        ),
        configuration='{"Version": 1.0, "CrawlerOutput": {"Partitions": {"AddOrUpdateBehavior": "InheritFromTable"}, "Tables": {"AddOrUpdateBehavior": "MergeNewColumns"}}, "Grouping": {"TableGroupingPolicy": "CombineCompatibleSchemas"}, "CreatePartitionIndex": true}',
        recrawl_policy=glue.CfnCrawler.RecrawlPolicyProperty(
            recrawl_behavior="CRAWL_EVERYTHING"
        ),
        schedule=glue.CfnCrawler.ScheduleProperty(
            schedule_expression="cron(45 4 * * ? *)"
        )
    )

    # Crawler for CloudWatch QuickSight Dashboard Visual
    crawler_cw_qs_dash_visual = glue.CfnCrawler(
        stack, "CrawlerCwQsDashVisual",
        name="crawler-cw-qs-dash-visual",
        role=f"arn:aws:iam::{stack.account}:role/QuickSuiteAdmin-{stack.account}",
        database_name="admin-console-2025",
        targets=glue.CfnCrawler.TargetsProperty(
            s3_targets=[
                glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://admin-suite-{stack.account}/cloudwatch/cw-qs-dash-visual/"
                )
            ]
        ),
        schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
            update_behavior="UPDATE_IN_DATABASE",
            delete_behavior="DEPRECATE_IN_DATABASE"
        ),
        configuration='{"Version": 1.0, "CrawlerOutput": {"Partitions": {"AddOrUpdateBehavior": "InheritFromTable"}, "Tables": {"AddOrUpdateBehavior": "MergeNewColumns"}}, "Grouping": {"TableGroupingPolicy": "CombineCompatibleSchemas"}, "CreatePartitionIndex": true}',
        recrawl_policy=glue.CfnCrawler.RecrawlPolicyProperty(
            recrawl_behavior="CRAWL_EVERYTHING"
        ),
        schedule=glue.CfnCrawler.ScheduleProperty(
            schedule_expression="cron(0 5 * * ? *)"
        )
    )

    # Crawler Trigger Job
    crawler_trigger_job = glue.CfnJob(
        stack, "CrawlerTriggerJob",
        name="crawler-trigger-job",
        role=f"arn:aws:iam::{stack.account}:role/QuickSuiteAdmin-{stack.account}",
        command=glue.CfnJob.JobCommandProperty(
            name="pythonshell",
            script_location=f"s3://{script_bucket_name.value_as_string}/glue/scripts/2025/crawler_trigger.py",
            python_version="3.9"
        ),
        default_arguments={
            "--job-language": "python",
            "--enable-metrics": ""
        },
        max_retries=0,
        timeout=60,
        glue_version="3.0",
        max_capacity=0.0625
    )

    return [crawler_cw_qs_ds, crawler_cw_qs_spice, crawler_cw_qs_qindex, crawler_cw_qs_qaction, crawler_cw_qs_dash_visual, crawler_trigger_job]