CREATE EXTERNAL TABLE IF NOT EXISTS NAMESPACE_PLACEHOLDER.machines (
  organizationId  STRING,
  principalId     STRING,
  name            STRING,
  serialNumber    STRING,
  ERID            STRING,
  make_name       STRING,
  type_name       STRING,
  isgType_name    STRING,
  model_name      STRING
)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
  LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3://STATIC_DATA_BUCKET_PLACEHOLDER/static/machines/'
TBLPROPERTIES ('skip.header.line.count' = '1');
