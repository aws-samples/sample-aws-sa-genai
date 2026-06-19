-- Raw telemetry: one row per 5-second machine reading.
-- Written by Firehose. ELT aggregates hourly → measurements.

CREATE TABLE IF NOT EXISTS NAMESPACE_PLACEHOLDER.telemetry (
  device_id           STRING,
  organization_id     STRING,
  event_time          TIMESTAMP,
  ingest_time         TIMESTAMP,
  machine_status      STRING,
  autotrac_active     BOOLEAN,
  section_control_on  BOOLEAN,
  autopath_on         BOOLEAN,
  fieldcruise_on      BOOLEAN,
  ipm_on              BOOLEAN,
  mfwd_on             BOOLEAN,
  rear_pto_on         BOOLEAN,
  wheel_slip_pct      DOUBLE,
  sample_interval_sec INT
)
LOCATION 's3://ICEBERG_BUCKET_PLACEHOLDER/NAMESPACE_PLACEHOLDER/telemetry/'
TBLPROPERTIES ('table_type' = 'ICEBERG');
