CREATE EXTERNAL TABLE `cw-metrics-qs-all`(
  `metric_stream_name` string COMMENT 'cw metric stream name', 
  `account_id` string COMMENT 'aws account id', 
  `region` string COMMENT 'aws region', 
  `namespace` string COMMENT 'metric namespace', 
  `metric_name` string COMMENT 'cw metric names', 
  `dimensions` struct<DatasetId:string,DashboardId:string,VisualId:string,SheetId:string> COMMENT 'dimensions for value', 
  `timestamp` bigint COMMENT 'event time', 
  `value` struct<max:double,min:double,sum:double,count:double> COMMENT 'metric value', 
  `unit` string COMMENT 'unit for value')
PARTITIONED BY ( 
  `partition_0` string, 
  `partition_1` string, 
  `partition_2` string, 
  `partition_3` string)
ROW FORMAT SERDE 
  'org.openx.data.jsonserde.JsonSerDe' 
WITH SERDEPROPERTIES ( 
  'paths'='account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value') 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://metricstreams-quickpartial-f8e2qm-2onoostc/'
TBLPROPERTIES (
  'classification'='json', 
  'compressionType'='none', 
  'objectCount'='9', 
  'partition_filtering.enabled'='true', 
  'typeOfData'='file')