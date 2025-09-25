CREATE EXTERNAL TABLE `cw-metrics-qs-dash-visual`(
  `metric_stream_name` string COMMENT 'cw metric stream name', 
  `account_id` string COMMENT 'aws account id', 
  `region` string COMMENT 'aws region', 
  `namespace` string COMMENT 'metric namespace', 
  `metric_name` string COMMENT 'cw metric names', 
  `dimensions` struct<DashboardId:string,SheetId:string,VisualId:string> COMMENT 'dimensions for value', 
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
  's3://metricstreams-cw-quicksight-all-z47qonru/'
TBLPROPERTIES (
  'classification'='json', 
  'compressionType'='none', 
  'partition_filtering.enabled'='true', 
  'typeOfData'='file')