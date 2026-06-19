"""
ELT Processor — Lambda function

Aggregates raw telemetry from the S3 Tables `telemetry` table into the
`measurements` table (one row per hour × machine × organization).

Triggered every hour by EventBridge (cron(5 * * * ? *) — 5 minutes past
the hour to allow the last Firehose batch to flush before aggregation).

Idempotency: the handler first DELETEs any existing rows for the target hour,
then INSERTs the fresh aggregation — safe to re-run for the same window.

The target hour can be overridden by passing {"hour_offset": N} in the event,
where N is the number of hours ago to reprocess (default 1 = the just-completed
hour).  Use N=0 to aggregate the current (in-progress) hour for testing.
"""

import os
import time
from datetime import datetime, timezone, timedelta

import boto3

ATHENA_DB = os.environ["ATHENA_DB"]
ATHENA_OUTPUT_BUCKET = os.environ["ATHENA_OUTPUT_BUCKET"]
AWS_REGION = os.environ.get("AWS_REGION_NAME", "us-east-1")

athena = boto3.client("athena", region_name=AWS_REGION)

OUTPUT_LOCATION = f"s3://{ATHENA_OUTPUT_BUCKET}/athena-results/elt/"


def _run_query(sql: str, description: str = "") -> str:
    """Submit an Athena query and block until it completes. Returns query execution ID."""
    print(f"Running Athena query: {description}")

    resp = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DB},
        ResultConfiguration={"OutputLocation": OUTPUT_LOCATION},
    )
    exec_id = resp["QueryExecutionId"]

    for attempt in range(120):
        status_resp = athena.get_query_execution(QueryExecutionId=exec_id)
        state = status_resp["QueryExecution"]["Status"]["State"]

        if state == "SUCCEEDED":
            print(f"  ✓ {description} ({exec_id})")
            return exec_id

        if state in ("FAILED", "CANCELLED"):
            reason = status_resp["QueryExecution"]["Status"].get(
                "StateChangeReason", "unknown"
            )
            raise RuntimeError(
                f"Athena query failed [{description}]: {reason} (ID: {exec_id})"
            )

        time.sleep(3)

    raise TimeoutError(f"Athena query timed out after 6 minutes: {exec_id}")


def lambda_handler(event, context):
    hour_offset = int(event.get("hour_offset", 1))

    now = datetime.now(timezone.utc)
    target_hour_start = (now - timedelta(hours=hour_offset)).replace(
        minute=0, second=0, microsecond=0
    )
    target_hour_end = target_hour_start + timedelta(hours=1)

    window_start = target_hour_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    window_end = target_hour_end.strftime("%Y-%m-%dT%H:%M:%SZ")

    target_year = target_hour_start.year
    target_doy = target_hour_start.timetuple().tm_yday
    target_hour = target_hour_start.hour

    print(
        f"ELT window: {window_start} → {window_end} "
        f"(year={target_year}, doy={target_doy}, hour={target_hour})"
    )

    # ---- Step 1: Delete existing rows for this hour (idempotency) -----------
    delete_sql = f"""
DELETE FROM {ATHENA_DB}.measurements
WHERE year        = BIGINT '{target_year}'
  AND day_of_year = BIGINT '{target_doy}'
  AND hour_of_day = BIGINT '{target_hour}'
"""
    _run_query(delete_sql, f"DELETE measurements for hour {target_hour}")

    # ---- Step 2: Insert fresh aggregation from telemetry --------------------
    insert_sql = f"""
INSERT INTO {ATHENA_DB}.measurements (
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
  organization_id                                                                              AS organizationId,
  device_id                                                                                    AS machine_id,
  CAST(year(event_time)        AS BIGINT)                                                      AS year,
  CAST(day_of_year(event_time) AS BIGINT)                                                      AS day_of_year,
  CAST(hour(event_time)        AS BIGINT)                                                      AS hour_of_day,

  CAST(SUM(CASE WHEN machine_status = 'WORKING'   THEN sample_interval_sec ELSE 0 END) AS DOUBLE) AS Machine_Utilization__Working__sec,
  CAST(SUM(CASE WHEN machine_status = 'IDLE'      THEN sample_interval_sec ELSE 0 END) AS DOUBLE) AS Machine_Utilization__Idle__sec,
  CAST(SUM(CASE WHEN machine_status = 'TRANSPORT' THEN sample_interval_sec ELSE 0 END) AS DOUBLE) AS Machine_Utilization__Transport__sec,

  CAST(SUM(CASE WHEN autotrac_active    = true  THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS AutoTrac__Active__sec,
  CAST(SUM(CASE WHEN autotrac_active    = false THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS AutoTrac__Inactive__sec,
  CAST(SUM(CASE WHEN section_control_on = true  THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS Section_Control__1__sec,
  CAST(SUM(CASE WHEN section_control_on = false THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS Section_Control__0__sec,
  CAST(SUM(CASE WHEN autopath_on        = true  THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS AutoPath___On__sec,
  CAST(SUM(CASE WHEN autopath_on        = false THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS AutoPath___Off__sec,
  CAST(SUM(CASE WHEN fieldcruise_on     = true  THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS FieldCruise__On__sec,
  CAST(SUM(CASE WHEN fieldcruise_on     = false THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS FieldCruise__Off__sec,
  CAST(SUM(CASE WHEN ipm_on             = true  THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS IPM__On__sec,
  CAST(SUM(CASE WHEN ipm_on             = false THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS IPM__Off__sec,
  CAST(SUM(CASE WHEN mfwd_on            = true  THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS MFWD__On__sec,
  CAST(SUM(CASE WHEN mfwd_on            = false THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS MFWD__Off__sec,
  CAST(SUM(CASE WHEN rear_pto_on        = true  THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS Rear_PTO__On__sec,
  CAST(SUM(CASE WHEN rear_pto_on        = false THEN sample_interval_sec ELSE 0 END) AS DOUBLE)   AS Rear_PTO__Off__sec,

  CAST(AVG(wheel_slip_pct) AS DOUBLE)                                                          AS Avg_Wheel_Slip____prcnt,
  current_timestamp                                                                              AS elt_processed_at

FROM {ATHENA_DB}.telemetry
WHERE event_time >= from_iso8601_timestamp('{window_start}')
  AND event_time <  from_iso8601_timestamp('{window_end}')

GROUP BY
  organization_id,
  device_id,
  year(event_time),
  day_of_year(event_time),
  hour(event_time)
"""
    _run_query(insert_sql, f"INSERT INTO measurements for hour {target_hour}")

    # ---- Step 3: Count rows inserted for observability ----------------------
    count_sql = f"""
SELECT COUNT(*) AS rows_inserted
FROM {ATHENA_DB}.measurements
WHERE year        = BIGINT '{target_year}'
  AND day_of_year = BIGINT '{target_doy}'
  AND hour_of_day = BIGINT '{target_hour}'
"""
    count_id = _run_query(count_sql, "COUNT rows inserted")
    result = athena.get_query_results(QueryExecutionId=count_id)
    rows_inserted = int(result["ResultSet"]["Rows"][1]["Data"][0]["VarCharValue"])

    print(f"ELT complete: {rows_inserted} measurement rows written for hour {window_start}")
    return {
        "window_start": window_start,
        "window_end": window_end,
        "rows_inserted": rows_inserted,
    }
