"""
S3 Tables Sync Lambda

Watermark-based incremental sync from iot_analytics.telemetry (standard Iceberg on S3)
into the S3 Tables-managed telemetry table via a cross-catalog Athena INSERT INTO.

Flow each invocation:
  1. Read last watermark from SSM Parameter Store
  2. INSERT rows where ingest_time is in (watermark, now - 2min]
  3. Advance watermark to now - 2min

The 2-minute buffer lets Firehose finish its 60-second commit cycle before we read.
On the very first invocation (no watermark), backlogs LOOKBACK_HOURS of data.

Triggered every 5 minutes via EventBridge.
"""

import os
import time
from datetime import datetime, timezone, timedelta

import boto3

AWS_REGION      = os.environ.get("AWS_REGION_NAME", "us-east-1")
SOURCE_DB       = os.environ["ATHENA_DB"]               # iot_analytics
S3TABLES_BUCKET = os.environ["S3TABLES_BUCKET"]          # e.g. iot-demo-tables-<account-id>
S3TABLES_NS     = os.environ.get("S3TABLES_NAMESPACE", "iot_analytics")
OUTPUT_BUCKET   = os.environ["ATHENA_OUTPUT_BUCKET"]
WATERMARK_PARAM = os.environ.get("WATERMARK_PARAM", "/iot-demo/s3tables-sync-watermark")
LOOKBACK_HOURS  = int(os.environ.get("LOOKBACK_HOURS", "24"))
BUFFER_MINUTES  = 2   # Firehose buffer headroom

athena = boto3.client("athena", region_name=AWS_REGION)
ssm    = boto3.client("ssm",    region_name=AWS_REGION)


def _run_athena(sql, label):
    resp = athena.start_query_execution(
        QueryString=sql,
        ResultConfiguration={"OutputLocation": f"s3://{OUTPUT_BUCKET}/s3tables-sync/"},
    )
    qid = resp["QueryExecutionId"]
    print(f"[{label}] started  query_id={qid}")
    while True:
        ex = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        state = ex["Status"]["State"]
        if state == "SUCCEEDED":
            mb = ex.get("Statistics", {}).get("DataScannedInBytes", 0) / 1_048_576
            print(f"[{label}] SUCCEEDED  scanned={mb:.2f} MB")
            return qid
        if state in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"[{label}] {state}: {ex['Status'].get('StateChangeReason','')}")
        time.sleep(3)


def lambda_handler(event, context):
    now_utc    = datetime.now(timezone.utc)
    sync_until = now_utc - timedelta(minutes=BUFFER_MINUTES)

    # --- watermark ---
    try:
        wm_iso  = ssm.get_parameter(Name=WATERMARK_PARAM)["Parameter"]["Value"]
        watermark = datetime.fromisoformat(wm_iso)
    except ssm.exceptions.ParameterNotFound:
        watermark = now_utc - timedelta(hours=LOOKBACK_HOURS)
        print(f"No watermark — backfilling from {watermark.isoformat()}")

    if watermark >= sync_until:
        msg = f"Nothing to sync (watermark={watermark.isoformat()} >= sync_until={sync_until.isoformat()})"
        print(msg)
        return {"status": "skipped", "watermark": watermark.isoformat()}

    wm_str    = watermark.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    until_str = sync_until.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    target    = f's3tablescatalog/{S3TABLES_BUCKET}'

    print(f"Syncing window: ({wm_str}, {until_str}]")

    # --- INSERT ---
    insert_sql = f"""INSERT INTO "{target}"."{S3TABLES_NS}"."telemetry"
SELECT
  device_id,
  organization_id,
  event_time,
  ingest_time,
  machine_status,
  autotrac_active,
  section_control_on,
  autopath_on,
  fieldcruise_on,
  ipm_on,
  mfwd_on,
  rear_pto_on,
  wheel_slip_pct,
  sample_interval_sec
FROM "AwsDataCatalog"."{SOURCE_DB}"."telemetry"
WHERE ingest_time > TIMESTAMP '{wm_str}'
  AND ingest_time <= TIMESTAMP '{until_str}'"""

    insert_qid = _run_athena(insert_sql, "INSERT")

    # --- row count for logging ---
    count_sql = f"""SELECT COUNT(*) AS cnt
FROM "{target}"."{S3TABLES_NS}"."telemetry"
WHERE ingest_time > TIMESTAMP '{wm_str}'
  AND ingest_time <= TIMESTAMP '{until_str}'"""
    count_qid = _run_athena(count_sql, "COUNT")
    rows = int(
        athena.get_query_results(QueryExecutionId=count_qid)
              ["ResultSet"]["Rows"][1]["Data"][0]["VarCharValue"]
    )

    # --- advance watermark ---
    ssm.put_parameter(
        Name=WATERMARK_PARAM,
        Value=sync_until.isoformat(),
        Type="String",
        Overwrite=True,
    )
    print(f"Watermark → {sync_until.isoformat()}  rows_inserted={rows}")

    return {
        "window_from":   wm_str,
        "window_to":     until_str,
        "rows_inserted": rows,
        "insert_query_id": insert_qid,
    }
