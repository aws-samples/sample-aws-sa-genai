CREATE EXTERNAL TABLE IF NOT EXISTS NAMESPACE_PLACEHOLDER.field_operation_products (
  field_operation_guid  STRING,
  product_name          STRING,
  organization_id       STRING
)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
  LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 's3://STATIC_DATA_BUCKET_PLACEHOLDER/static/field_operation_products/'
TBLPROPERTIES ('skip.header.line.count' = '1');
