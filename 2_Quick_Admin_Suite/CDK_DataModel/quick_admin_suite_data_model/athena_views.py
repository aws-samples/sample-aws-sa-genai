from aws_cdk import aws_athena as athena

def create_athena_views(stack, cur_source_table):
    """Create Athena named queries (views)"""
    
    # QuickSight CRUD Events View
    quicksight_crud_events_view = athena.CfnNamedQuery(
        stack, "QuickSightCrudEventsView",
        database="admin-console-2025",
        description="View for QuickSight CRUD events from CloudTrail logs",
        name="quicksight_crud_events_view",
        query_string="""CREATE OR REPLACE VIEW quicksight_crud_events AS 
SELECT *
FROM cloudtrail_logs_pp
WHERE (
  eventsource = 'quicksight.amazonaws.com'
  AND parse_datetime(eventtime, 'yyyy-MM-dd''T''HH:mm:ss''Z') >= (current_timestamp - INTERVAL '40' DAY)
  AND REGEXP_LIKE(eventname, '^(Create|Update|Delete)')
)""",
        work_group="primary"
    )

    # QuickSight QueryDatabase Events View
    quicksight_querydb_events_view = athena.CfnNamedQuery(
        stack, "QuickSightQueryDbEventsView",
        database="admin-console-2025",
        description="View for QuickSight QueryDatabase events from CloudTrail logs",
        name="quicksight_querydb_events_view",
        query_string="""CREATE OR REPLACE VIEW quicksight_querydb_events AS 
SELECT
  *
, JSON_EXTRACT_SCALAR(serviceeventdetails, '$.eventRequestDetails.dataSourceId') datasourceid
, JSON_EXTRACT_SCALAR(serviceeventdetails, '$.eventRequestDetails.queryId') queryid
, JSON_EXTRACT_SCALAR(serviceeventdetails, '$.eventRequestDetails.resourceId') dashboard_analysis
, JSON_EXTRACT_SCALAR(serviceeventdetails, '$.eventRequestDetails.dataSetId') datasetid
, JSON_EXTRACT_SCALAR(serviceeventdetails, '$.eventRequestDetails.dataSetMode') datasetmode
FROM cloudtrail_logs_pp
WHERE ((eventsource = 'quicksight.amazonaws.com') AND (parse_datetime(eventtime, 'yyyy-MM-dd''T''HH:mm:ss''Z') >= (current_timestamp - INTERVAL '40' DAY)) AND (eventname = 'QueryDatabase'))""",
        work_group="primary"
    )

    # QuickSight Usage CUR View
    qs_usage_cur_view = athena.CfnNamedQuery(
        stack, "QsUsageCurView",
        database="admin-console-2025",
        description="QuickSight usage and cost analysis view from CUR data",
        name="qs_usage_cur_vw",
        query_string=f"""CREATE OR REPLACE VIEW "qs_usage_cur_vw" AS 
SELECT
  bill_payer_account_id
, line_item_usage_account_id
, concat(DATE_FORMAT(line_item_usage_start_date, '%Y-%m'), '-01') month_line_item_usage_start_date
, line_item_usage_type
, (CASE WHEN (LOWER(line_item_usage_type) LIKE 'qs-user-enterprise%') THEN 'Users - Enterprise' WHEN (LOWER(line_item_usage_type) LIKE 'qs-user-standard%') THEN 'Users - Standard' WHEN (LOWER(line_item_usage_type) LIKE 'qs-reader%') THEN 'Reader Usage' WHEN (LOWER(line_item_usage_type) LIKE '%spice') THEN 'SPICE' WHEN (LOWER(line_item_usage_type) LIKE '%alerts%') THEN 'Alerts' WHEN (LOWER(line_item_usage_type) LIKE '%-q%') THEN 'QuickSight Q' WHEN (LOWER(line_item_usage_type) LIKE '%-report%') THEN 'Paginated Reporting' WHEN (LOWER(line_item_usage_type) LIKE '%-reader-pro%') THEN 'Reader PRO' WHEN (LOWER(line_item_usage_type) LIKE '%-author-pro%') THEN 'Author PRO' WHEN (LOWER(line_item_usage_type) LIKE '%-reader-enterprise%') THEN 'Reader Usage' ELSE line_item_usage_type END) qs_usage_type
, line_item_line_item_description
, line_item_line_item_type
, product['group'] product_group
, pricing_unit
, line_item_resource_id
, product_usagetype
, line_item_unblended_rate
, line_item_blended_rate
, line_item_operation
, SUM(CAST(line_item_usage_amount AS DOUBLE)) sum_line_item_usage_amount
, SUM(CAST(line_item_unblended_cost AS DECIMAL(16, 8))) sum_line_item_unblended_cost
, SUM(CAST(line_item_blended_cost AS DECIMAL(16, 8))) line_item_blended_cost
FROM {cur_source_table.value_as_string}
WHERE ((product['product_name'] = 'Amazon QuickSight') AND (line_item_line_item_type IN ('DiscountedUsage', 'Usage')))
GROUP BY bill_payer_account_id, line_item_usage_account_id, DATE_FORMAT(line_item_usage_start_date, '%Y-%m'), 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
ORDER BY month_line_item_usage_start_date ASC, sum_line_item_unblended_cost DESC, month_line_item_usage_start_date ASC, sum_line_item_unblended_cost DESC""",
        work_group="primary"
    )

    # CloudWatch QuickSight Dataset Pivot View
    cw_qs_ds_pivot_view = athena.CfnNamedQuery(
        stack, "CwQsDsPivotView",
        database="admin-console-2025",
        description="Pivot view for CloudWatch QuickSight dataset metrics",
        name="cw_qs_ds_pivot_view",
        query_string=f"""CREATE OR REPLACE VIEW cw_qs_ds_pivot AS 
SELECT
  timestamp
, account_id
, region
, dimensions.datasetid datasetid
, CAST(MAX((CASE WHEN (metric_name = 'IngestionErrorCount') THEN value.sum END)) AS INTEGER) IngestionErrorCount
, MAX((CASE WHEN (metric_name = 'IngestionErrorCount') THEN unit END)) IngestionErrorCount_Unit
, CAST(MAX((CASE WHEN (metric_name = 'IngestionInvocationCount') THEN value.sum END)) AS INTEGER) IngestionInvocationCount
, MAX((CASE WHEN (metric_name = 'IngestionInvocationCount') THEN unit END)) IngestionInvocationCount_Unit
, CAST(MAX((CASE WHEN (metric_name = 'IngestionLatency') THEN value.sum END)) AS DOUBLE) IngestionLatency
, MAX((CASE WHEN (metric_name = 'IngestionLatency') THEN unit END)) IngestionLatency_Unit
, CAST(MAX((CASE WHEN (metric_name = 'IngestionRowCount') THEN value.sum END)) AS INTEGER) IngestionRowCount
, MAX((CASE WHEN (metric_name = 'IngestionRowCount') THEN unit END)) IngestionRowCount_Unit
FROM cw_qs_ds_{stack.account}
GROUP BY timestamp, account_id, region, dimensions
ORDER BY timestamp ASC, account_id ASC, region ASC""",
        work_group="primary"
    )

    return [quicksight_crud_events_view, quicksight_querydb_events_view, qs_usage_cur_view, cw_qs_ds_pivot_view]