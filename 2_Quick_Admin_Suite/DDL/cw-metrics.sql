CREATE EXTERNAL TABLE `cw-metrics`(
  `metric_stream_name` string COMMENT 'from deserializer', 
  `account_id` string COMMENT 'from deserializer', 
  `region` string COMMENT 'from deserializer', 
  `namespace` string COMMENT 'from deserializer', 
  `metric_name` string COMMENT 'from deserializer', 
  `dimensions` map<string,string>,
  `timestamp` timestamp COMMENT 'from deserializer', 
  `value` struct<max:double,min:double,sum:double,count:double> COMMENT 'from deserializer', 
  `unit` string COMMENT 'from deserializer')
PARTITIONED BY (
    month string,
    day string,
    hour string
)
ROW FORMAT SERDE 
  'org.openx.data.jsonserde.JsonSerDe' 
WITH SERDEPROPERTIES ( 
  'paths'='account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value') 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://athena-cw-metrics-499080683179/2025/'
TBLPROPERTIES (
  'classification'='json', 
  'compressionType'='none', 
  'partition_filtering.enabled'='true', 
  'typeOfData'='file',
  "projection.enabled"="false")