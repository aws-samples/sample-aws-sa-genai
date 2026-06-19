CREATE EXTERNAL TABLE IF NOT EXISTS NAMESPACE_PLACEHOLDER.scuds (
  organizationId              STRING,
  fieldOperationGUID          STRING,
  machineGUID                 STRING,
  machine_vin                 STRING,
  machine_id                  STRING,
  field_guid                  STRING,
  operation_type              STRING,
  crop                        STRING,
  operator_name               STRING,
  farm_guid                   STRING,
  product_name                STRING,
  `operationalSummary.clientGuids` STRING
)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
  LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3://STATIC_DATA_BUCKET_PLACEHOLDER/static/scuds/'
TBLPROPERTIES ('skip.header.line.count' = '1');
