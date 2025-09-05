CREATE OR REPLACE VIEW "cw-metrics-qs-all-pivot" AS 
SELECT
  timestamp
, account_id
, region
, dimensions.datasetid dataset_id
, CAST(MAX((CASE WHEN (metric_name = 'DashboardViewCount') THEN value.sum END)) AS INTEGER) DashboardViewCount
, MAX((CASE WHEN (metric_name = 'DashboardViewCount') THEN unit END)) DashboardViewCount_Unit
, CAST(MAX((CASE WHEN (metric_name = 'DashboardViewLoadTime') THEN value.sum END)) AS DOUBLE) DashboardViewLoadTime
, MAX((CASE WHEN (metric_name = 'DashboardViewLoadTime') THEN unit END)) DashboardViewLoadTime_Unit
, CAST(MAX((CASE WHEN (metric_name = 'IngestionErrorCount') THEN value.sum END)) AS INTEGER) IngestionErrorCount
, MAX((CASE WHEN (metric_name = 'IngestionErrorCount') THEN unit END)) IngestionErrorCount_Unit
, CAST(MAX((CASE WHEN (metric_name = 'IngestionInvocationCount') THEN value.sum END)) AS INTEGER) IngestionInvocationCount
, MAX((CASE WHEN (metric_name = 'IngestionInvocationCount') THEN unit END)) IngestionInvocationCount_Unit
, CAST(MAX((CASE WHEN (metric_name = 'IngestionLatency') THEN value.sum END)) AS DOUBLE) IngestionLatency
, MAX((CASE WHEN (metric_name = 'IngestionLatency') THEN unit END)) IngestionLatency_Unit
, CAST(MAX((CASE WHEN (metric_name = 'IngestionRowCount') THEN value.sum END)) AS INTEGER) IngestionRowCount
, MAX((CASE WHEN (metric_name = 'IngestionRowCount') THEN unit END)) IngestionRowCount_Unit
, CAST(MAX((CASE WHEN (metric_name = 'VisualLoadTime') THEN value.sum END)) AS DOUBLE) VisualLoadTime
, MAX((CASE WHEN (metric_name = 'VisualLoadTime') THEN unit END)) VisualLoadTime_Unit
, CAST(MAX((CASE WHEN (metric_name = 'VisualLoadErrorCount') THEN value.sum END)) AS INTEGER) VisualLoadErrorCount
, MAX((CASE WHEN (metric_name = 'VisualLoadErrorCount') THEN unit END)) VisualLoadErrorCount_Unit
, CAST(MAX((CASE WHEN (metric_name = 'SPICECapacityLimitInMB') THEN value.sum END)) AS DOUBLE) SPICECapacityLimitInMB
, MAX((CASE WHEN (metric_name = 'SPICECapacityLimitInMB') THEN unit END)) SPICECapacityLimitInMB_Unit
, CAST(MAX((CASE WHEN (metric_name = 'SPICECapacityConsumedInMB') THEN value.sum END)) AS DOUBLE) SPICECapacityConsumedInMB
, MAX((CASE WHEN (metric_name = 'SPICECapacityConsumedInMB') THEN unit END)) SPICECapacityConsumedInMB_Unit
FROM
  "admin-console-2025"."metricstreams_quickpartial_f8e2qm_2onoostc"
GROUP BY timestamp, account_id, region, dimensions
ORDER BY timestamp ASC, account_id ASC, region ASC
