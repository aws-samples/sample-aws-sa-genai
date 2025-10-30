from aws_cdk import aws_glue as glue

def create_crawlers(stack):
    """Create Glue crawlers for CloudWatch metrics"""
    
    # Crawler for CloudWatch QuickSight Dataset
    crawler_cw_qs_ds = glue.CfnCrawler(
        stack, "CrawlerCwQsDs",
        name="crawler-cw-qs-ds",
        role=f"arn:aws:iam::{stack.account}:role/QuickSightAdminConsole2025",
        database_name="admin-console-2025",
        targets=glue.CfnCrawler.TargetsProperty(
            s3_targets=[
                glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://cw-qs-ds-{stack.account}/"
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
        )
    )

    # Crawler for CloudWatch QuickSight SPICE
    crawler_cw_qs_spice = glue.CfnCrawler(
        stack, "CrawlerCwQsSpice",
        name="crawler-cw-qs-spice",
        role=f"arn:aws:iam::{stack.account}:role/QuickSightAdminConsole2025",
        database_name="admin-console-2025",
        targets=glue.CfnCrawler.TargetsProperty(
            s3_targets=[
                glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://cw-qs-spice-{stack.account}/"
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
        )
    )

    # Crawler for CloudWatch QuickSight Dashboard Visual
    crawler_cw_qs_dash_visual = glue.CfnCrawler(
        stack, "CrawlerCwQsDashVisual",
        name="crawler-cw-qs-dash-visual",
        role=f"arn:aws:iam::{stack.account}:role/QuickSightAdminConsole2025",
        database_name="admin-console-2025",
        targets=glue.CfnCrawler.TargetsProperty(
            s3_targets=[
                glue.CfnCrawler.S3TargetProperty(
                    path=f"s3://cw-qs-dash-visual-{stack.account}/"
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
        )
    )

    # Scheduled crawlers for partition management
    crawler_cw_qs_ds_add_part = glue.CfnCrawler(
        stack, "CrawlerCwQsDsAddPart",
        name="crawler-cw-qs-ds-add-part",
        role=f"arn:aws:iam::{stack.account}:role/QuickSightAdminConsole2025",
        database_name="admin-console-2025",
        targets=glue.CfnCrawler.TargetsProperty(
            catalog_targets=[
                glue.CfnCrawler.CatalogTargetProperty(
                    database_name="admin-console-2025",
                    tables=[f"cw_qs_ds_{stack.account}"]
                )
            ]
        ),
        schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
            update_behavior="UPDATE_IN_DATABASE",
            delete_behavior="LOG"
        ),
        schedule=glue.CfnCrawler.ScheduleProperty(
            schedule_expression="cron(0 * * * ? *)"
        ),
        configuration='{"Version": 1.0, "CrawlerOutput": {"Partitions": {"AddOrUpdateBehavior": "InheritFromTable"}, "Tables": {"AddOrUpdateBehavior": "MergeNewColumns"}}}'
    )

    return [crawler_cw_qs_ds, crawler_cw_qs_spice, crawler_cw_qs_dash_visual, crawler_cw_qs_ds_add_part]