CREATE EXTERNAL TABLE `cw_qs_qaction`(
  `metric_stream_name` string COMMENT 'Name of the CloudWatch metric stream', 
  `account_id` string COMMENT 'AWS account ID', 
  `region` string COMMENT 'AWS region', 
  `namespace` string COMMENT 'CloudWatch namespace (AWS/QuickSight)', 
  `metric_name` string COMMENT 'CloudWatch metric name', 
  `dimensions` struct<ActionConnectorId:string,ActionConnectorType:string,ActionId:string,InvokeErrorCode:string> COMMENT 'QuickSight Q Action identifiers and error codes', 
  `timestamp` bigint COMMENT 'Metric timestamp in epoch milliseconds', 
  `value` struct<max:double,min:double,sum:double,count:double> COMMENT 'Metric statistical values', 
  `unit` string COMMENT 'Metric unit of measurement')
PARTITIONED BY ( 
  `year` string,
  `month` string,
  `day` string,
  `hour` string)
ROW FORMAT SERDE 
  'org.openx.data.jsonserde.JsonSerDe' 
WITH SERDEPROPERTIES ( 
  'paths'='account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value') 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://cw-qs-qaction-905178920046/'
TBLPROPERTIES (
  'projection.enabled'='true',
  'projection.year.type'='integer',
  'projection.year.range'='2024,2030',
  'projection.month.type'='integer',
  'projection.month.range'='01,12',
  'projection.month.digits'='2',
  'projection.day.type'='integer',
  'projection.day.range'='01,31',
  'projection.day.digits'='2',
  'projection.hour.type'='integer',
  'projection.hour.range'='00,23',
  'projection.hour.digits'='2',
  'storage.location.template'='s3://cw-qs-qaction-905178920046/${year}/${month}/${day}/${hour}/',
  'classification'='json',
  'partition_filtering.enabled'='true',
  'typeOfData'='file')