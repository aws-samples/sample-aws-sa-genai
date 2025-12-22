CREATE EXTERNAL TABLE `qs_chat_log`(
  `user_arn` string COMMENT 'from deserializer', 
  `user_type` string COMMENT 'from deserializer', 
  `status_code` string COMMENT 'from deserializer', 
  `conversation_id` string COMMENT 'from deserializer', 
  `system_message_id` string COMMENT 'from deserializer', 
  `message_scope` string COMMENT 'from deserializer', 
  `user_message_id` string COMMENT 'from deserializer', 
  `user_message` string COMMENT 'from deserializer', 
  `agent_id` string COMMENT 'from deserializer', 
  `flow_id` string COMMENT 'from deserializer', 
  `system_text_message` string COMMENT 'from deserializer', 
  `user_selected_resources` array<struct<resourceid:string,resourcetype:string>> COMMENT 'from deserializer', 
  `action_connectors` array<struct<actionconnectorid:string>> COMMENT 'from deserializer', 
  `cited_resource` array<struct<citedresourcetype:string,citedresourceid:string,citedresourcename:string>> COMMENT 'from deserializer', 
  `file_attachment` array<string> COMMENT 'from deserializer', 
  `resource_arn` string COMMENT 'from deserializer', 
  `event_timestamp` bigint COMMENT 'from deserializer', 
  `logtype` string COMMENT 'from deserializer', 
  `accountid` string COMMENT 'from deserializer')
PARTITIONED BY ( 
  `region` string,
  `account_id` string,
  `year` string,
  `month` string,
  `day` string,
  `hour` string)
ROW FORMAT SERDE 
  'org.openx.data.jsonserde.JsonSerDe' 
WITH SERDEPROPERTIES ( 
  'paths'='accountId,action_connectors,agent_id,cited_resource,conversation_id,event_timestamp,file_attachment,flow_id,logType,message_scope,resource_arn,status_code,system_message_id,system_text_message,user_arn,user_message,user_message_id,user_selected_resources,user_type') 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://admin-console-new-905178920046/monitoring/quicksight/cw-vended-log/chat-log/AWSLogs/905178920046/quicksuitelogs/'
TBLPROPERTIES (
  'projection.enabled'='true',
  'projection.region.type'='enum',
  'projection.region.values'='us-east-1,us-east-2,us-west-2',
  'projection.account_id.type'='enum',
  'projection.account_id.values'='905178920046',
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
  'storage.location.template'='s3://admin-console-new-905178920046/monitoring/quicksight/cw-vended-log/chat-log/AWSLogs/905178920046/quicksuitelogs/${region}/${account_id}/${year}/${month}/${day}/${hour}/',
  'classification'='json', 
  'compressionType'='gzip', 
  'partition_filtering.enabled'='true', 
  'typeOfData'='file')