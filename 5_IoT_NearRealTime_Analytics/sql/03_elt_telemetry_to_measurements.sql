-- =============================================================================
-- ELT: Telemetry → Measurements (hourly aggregation)
--
-- This query is parameterized. The ELT Lambda substitutes:
--   {window_start}  → ISO 8601 timestamp of the hour's start  (e.g. 2025-06-17T14:00:00Z)
--   {window_end}    → ISO 8601 timestamp of the hour's end    (e.g. 2025-06-17T15:00:00Z)
--   {namespace}     → iot_analytics
--
-- Logic:
--   1. Delete any existing measurements row for the same (org, machine, hour)
--      to ensure idempotency when ELT reruns for the same window.
--   2. INSERT the aggregated result from telemetry for that window.
--
-- Run as two separate Athena queries (DELETE then INSERT) because Athena
-- does not support MERGE INTO on S3 Tables in all regions as of mid-2025.
-- =============================================================================

-- ---- Query 1: DELETE existing rows for the target hour (idempotency) --------

DELETE FROM {namespace}.measurements
WHERE year       = CAST(year(from_iso8601_timestamp('{window_start}')) AS BIGINT)
  AND day_of_year = CAST(day_of_year(from_iso8601_timestamp('{window_start}')) AS BIGINT)
  AND hour_of_day = CAST(hour(from_iso8601_timestamp('{window_start}')) AS BIGINT);


-- ---- Query 2: INSERT aggregated telemetry rows for the target hour ----------

INSERT INTO {namespace}.measurements (
  organizationId,
  machine_id,
  year,
  day_of_year,
  hour_of_day,
  Machine_Utilization__Working__sec,
  Machine_Utilization__Idle__sec,
  Machine_Utilization__Transport__sec,
  AutoTrac__Active__sec,
  AutoTrac__Inactive__sec,
  Section_Control__1__sec,
  Section_Control__0__sec,
  AutoPath___On__sec,
  AutoPath___Off__sec,
  FieldCruise__On__sec,
  FieldCruise__Off__sec,
  IPM__On__sec,
  IPM__Off__sec,
  MFWD__On__sec,
  MFWD__Off__sec,
  Rear_PTO__On__sec,
  Rear_PTO__Off__sec,
  Avg_Wheel_Slip____prcnt,
  elt_processed_at
)
SELECT
  organization_id                                                                         AS organizationId,
  device_id                                                                               AS machine_id,
  CAST(year(event_time)        AS BIGINT)                                                 AS year,
  CAST(day_of_year(event_time) AS BIGINT)                                                 AS day_of_year,
  CAST(hour(event_time)        AS BIGINT)                                                 AS hour_of_day,

  -- Utilization states
  CAST(SUM(CASE WHEN machine_status = 'WORKING'   THEN sample_interval_sec ELSE 0 END) AS DOUBLE) AS Machine_Utilization__Working__sec,
  CAST(SUM(CASE WHEN machine_status = 'IDLE'      THEN sample_interval_sec ELSE 0 END) AS DOUBLE) AS Machine_Utilization__Idle__sec,
  CAST(SUM(CASE WHEN machine_status = 'TRANSPORT' THEN sample_interval_sec ELSE 0 END) AS DOUBLE) AS Machine_Utilization__Transport__sec,

  -- Feature timers
  CAST(SUM(CASE WHEN autotrac_active    THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS AutoTrac__Active__sec,
  CAST(SUM(CASE WHEN NOT autotrac_active    THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS AutoTrac__Inactive__sec,
  CAST(SUM(CASE WHEN section_control_on THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS Section_Control__1__sec,
  CAST(SUM(CASE WHEN NOT section_control_on THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS Section_Control__0__sec,
  CAST(SUM(CASE WHEN autopath_on        THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS AutoPath___On__sec,
  CAST(SUM(CASE WHEN NOT autopath_on        THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS AutoPath___Off__sec,
  CAST(SUM(CASE WHEN fieldcruise_on     THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS FieldCruise__On__sec,
  CAST(SUM(CASE WHEN NOT fieldcruise_on     THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS FieldCruise__Off__sec,
  CAST(SUM(CASE WHEN ipm_on             THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS IPM__On__sec,
  CAST(SUM(CASE WHEN NOT ipm_on             THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS IPM__Off__sec,
  CAST(SUM(CASE WHEN mfwd_on            THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS MFWD__On__sec,
  CAST(SUM(CASE WHEN NOT mfwd_on            THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS MFWD__Off__sec,
  CAST(SUM(CASE WHEN rear_pto_on        THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS Rear_PTO__On__sec,
  CAST(SUM(CASE WHEN NOT rear_pto_on        THEN sample_interval_sec ELSE 0 END) AS DOUBLE)  AS Rear_PTO__Off__sec,

  -- Quality
  CAST(AVG(wheel_slip_pct) AS DOUBLE)                                                    AS Avg_Wheel_Slip____prcnt,
  current_timestamp                                                                        AS elt_processed_at

FROM {namespace}.telemetry
WHERE event_time >= from_iso8601_timestamp('{window_start}')
  AND event_time <  from_iso8601_timestamp('{window_end}')

GROUP BY
  organization_id,
  device_id,
  year(event_time),
  day_of_year(event_time),
  hour(event_time);
