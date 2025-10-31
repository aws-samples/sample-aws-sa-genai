from aws_cdk import (
    Stack,
    CfnParameter,
    aws_athena as athena,
)
from constructs import Construct

class QuickAdminSuiteAthenaViewsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Parameters
        cur_source_table = CfnParameter(
            self, "CURSourceTable",
            type="String",
            description="Provide CUR database and table name with format database.table_name as it exists in your account (e.g., billing.cur)",
            allowed_pattern="^[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+$",
            constraint_description="Must be in format database.table_name",
            min_length=3
        )

        # QuickSight CRUD Events View
        quicksight_crud_events_view = athena.CfnNamedQuery(
            self, "QuickSightCrudEventsView",
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
            self, "QuickSightQueryDbEventsView",
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
            self, "QsUsageCurView",
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

        # CloudWatch Dataset Pivot View
        cw_qs_ds_pivot_view = athena.CfnNamedQuery(
            self, "CwQsDsPivotView",
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
FROM cw_qs_ds_{self.account}
GROUP BY timestamp, account_id, region, dimensions
ORDER BY timestamp ASC, account_id ASC, region ASC""",
            work_group="primary"
        )

        # CloudWatch Dashboard Visual Pivot View
        cw_qs_dash_visual_pivot_view = athena.CfnNamedQuery(
            self, "CwQsDashVisualPivotView",
            database="admin-console-2025",
            description="Pivot view for CloudWatch QuickSight dashboard visual metrics",
            name="cw_qs_dash_visual_pivot_view",
            query_string=f"""CREATE OR REPLACE VIEW cw_qs_dash_visual_pivot AS 
SELECT
  timestamp
, account_id
, region
, dimensions.dashboardid dashboardid
, dimensions.sheetid sheetid
, dimensions.visualid visualid
, CAST(MAX((CASE WHEN (metric_name = 'DashboardViewCount') THEN value.sum END)) AS INTEGER) DashboardViewCount
, MAX((CASE WHEN (metric_name = 'DashboardViewCount') THEN unit END)) DashboardViewCount_Unit
, CAST(MAX((CASE WHEN (metric_name = 'DashboardViewLoadTime') THEN value.sum END)) AS DOUBLE) DashboardViewLoadTime
, MAX((CASE WHEN (metric_name = 'DashboardViewLoadTime') THEN unit END)) DashboardViewLoadTime_Unit
, CAST(MAX((CASE WHEN (metric_name = 'VisualLoadTime') THEN value.sum END)) AS DOUBLE) VisualLoadTime
, MAX((CASE WHEN (metric_name = 'VisualLoadTime') THEN unit END)) VisualLoadTime_Unit
, CAST(MAX((CASE WHEN (metric_name = 'VisualLoadErrorCount') THEN value.sum END)) AS INTEGER) VisualLoadErrorCount
, MAX((CASE WHEN (metric_name = 'VisualLoadErrorCount') THEN unit END)) VisualLoadErrorCount_Unit
FROM cw_qs_dash_visual_{self.account}
GROUP BY timestamp, account_id, region, dimensions
ORDER BY timestamp ASC, account_id ASC, region ASC""",
            work_group="primary"
        )

        # CloudWatch SPICE Pivot View
        cw_qs_spice_pivot_view = athena.CfnNamedQuery(
            self, "CwQsSpicePivotView",
            database="admin-console-2025",
            description="Pivot view for CloudWatch QuickSight SPICE metrics",
            name="cw_qs_spice_pivot_view",
            query_string=f"""CREATE OR REPLACE VIEW cw_qs_spice_pivot AS 
SELECT
  timestamp
, account_id
, region
, CAST(MAX((CASE WHEN (metric_name = 'SPICECapacityLimitInMB') THEN value.sum END)) AS DOUBLE) SPICECapacityLimitInMB
, MAX((CASE WHEN (metric_name = 'SPICECapacityLimitInMB') THEN unit END)) SPICECapacityLimitInMB_Unit
, CAST(MAX((CASE WHEN (metric_name = 'SPICECapacityConsumedInMB') THEN value.sum END)) AS DOUBLE) SPICECapacityConsumedInMB
, MAX((CASE WHEN (metric_name = 'SPICECapacityConsumedInMB') THEN unit END)) SPICECapacityConsumedInMB_Unit
FROM cw_qs_spice_{self.account}
GROUP BY timestamp, account_id, region
ORDER BY timestamp ASC, account_id ASC, region ASC""",
            work_group="primary"
        )

        # CloudWatch Q Index Pivot View
        cw_qs_qindex_pivot_view = athena.CfnNamedQuery(
            self, "CwQsQIndexPivotView",
            database="admin-console-2025",
            description="Pivot view for CloudWatch QuickSight Q Index metrics",
            name="cw_qs_qindex_pivot_view",
            query_string=f"""CREATE OR REPLACE VIEW cw_qs_qindex_pivot AS 
SELECT
  timestamp
, account_id
, region
, dimensions.quickinstanceid quickinstanceid
, CAST(MAX((CASE WHEN (metric_name = 'QuickIndexDocumentCount') THEN value.sum END)) AS INTEGER) QuickIndexDocumentCount
, MAX((CASE WHEN (metric_name = 'QuickIndexDocumentCount') THEN unit END)) QuickIndexDocumentCount_Unit
, CAST(MAX((CASE WHEN (metric_name = 'QuickIndexExtractedTextSize') THEN value.sum END)) AS DOUBLE) QuickIndexExtractedTextSize
, MAX((CASE WHEN (metric_name = 'QuickIndexExtractedTextSize') THEN unit END)) QuickIndexExtractedTextSize_Unit
FROM cw_qs_qindex_{self.account}
GROUP BY timestamp, account_id, region, dimensions
ORDER BY timestamp ASC, account_id ASC, region ASC""",
            work_group="primary"
        )

        # Combined Dataset Info View
        qs_ds_info_combined_view = athena.CfnNamedQuery(
            self, "QsDsInfoCombinedView",
            database="admin-console-2025",
            description="Combined view of dataset properties and dataset info",
            name="qs_ds_info_combined_view",
            query_string="""CREATE OR REPLACE VIEW qs_ds_info_combined AS 
SELECT 
    t.*
FROM (
    SELECT 
        dsp.*,
        dsi.data_source_name,
        dsi.data_source_id,
        dsi.catalog,
        dsi."sqlname/schema",
        dsi."sqlquery/table_name"
    FROM datasets_properties AS dsp
    JOIN (
        SELECT aws_region, dataset_id, data_source_name, data_source_id, catalog, 
               "sqlname/schema", "sqlquery/table_name"
        FROM datasets_info
    ) AS dsi
    ON dsp.dataset_id = dsi.dataset_id AND dsp.region = dsi.aws_region
) AS t
GROUP BY 
    1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25
ORDER BY t.region ASC, t.dataset_id ASC""",
            work_group="primary"
        )