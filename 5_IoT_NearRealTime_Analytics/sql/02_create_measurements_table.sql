-- Measurements: one row per hour × machine × organization.
-- Populated by ELT Lambda from telemetry. Schema matches measurements.csv.

CREATE TABLE IF NOT EXISTS NAMESPACE_PLACEHOLDER.measurements (
  organizationId                              STRING,
  machine_id                                  STRING,
  year                                        BIGINT,
  day_of_year                                 BIGINT,
  hour_of_day                                 BIGINT,
  Machine_Utilization__Working__sec           DOUBLE,
  Machine_Utilization__Idle__sec              DOUBLE,
  Machine_Utilization__Transport__sec         DOUBLE,
  AutoTrac__Active__sec                       DOUBLE,
  AutoTrac__Inactive__sec                     DOUBLE,
  Section_Control__1__sec                     DOUBLE,
  Section_Control__0__sec                     DOUBLE,
  AutoPath___On__sec                          DOUBLE,
  AutoPath___Off__sec                         DOUBLE,
  FieldCruise__On__sec                        DOUBLE,
  FieldCruise__Off__sec                       DOUBLE,
  IPM__On__sec                                DOUBLE,
  IPM__Off__sec                               DOUBLE,
  MFWD__On__sec                               DOUBLE,
  MFWD__Off__sec                              DOUBLE,
  Rear_PTO__On__sec                           DOUBLE,
  Rear_PTO__Off__sec                          DOUBLE,
  Avg_Wheel_Slip____prcnt                     DOUBLE,
  elt_processed_at                            TIMESTAMP
)
LOCATION 's3://ICEBERG_BUCKET_PLACEHOLDER/NAMESPACE_PLACEHOLDER/measurements/'
TBLPROPERTIES ('table_type' = 'ICEBERG');
