CREATE EXTERNAL TABLE `qs_feedback_log`(
  `user_arn` string COMMENT 'Amazon QuickSight user ARN who provided feedback', 
  `user_type` string COMMENT 'QuickSight user type (ADMIN_PRO, AUTHOR_PRO, etc.)', 
  `status_code` string COMMENT 'Status of the feedback event delivery', 
  `conversation_id` string COMMENT 'Unique identifier of the conversation', 
  `research_id` string COMMENT 'Unique identifier of the research session', 
  `system_message_id` string COMMENT 'System generated message identifier', 
  `user_message_id` string COMMENT 'User message identifier being rated', 
  `feedback_type` string COMMENT 'Type of feedback provided (thumbs up/down, rating)', 
  `feedback_reason` string COMMENT 'Reason or category for the feedback', 
  `rating` string COMMENT 'Numerical or categorical rating provided', 
  `resource_arn` string COMMENT 'QuickSight resource ARN associated with feedback', 
  `event_timestamp` bigint COMMENT 'Timestamp when feedback was provided (epoch ms)', 
  `logtype` string COMMENT 'Type of log entry (Feedback)', 
  `accountid` string COMMENT 'AWS account ID where feedback occurred')
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
  'paths'='accountId,conversation_id,event_timestamp,feedback_reason,feedback_type,logType,rating,research_id,resource_arn,status_code,system_message_id,user_arn,user_message_id,user_type') 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://admin-console-new-905178920046/monitoring/quicksight/cw-vended-log/feedback-log/AWSLogs/905178920046/quicksuitelogs/'
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
  'storage.location.template'='s3://admin-console-new-905178920046/monitoring/quicksight/cw-vended-log/feedback-log/AWSLogs/905178920046/quicksuitelogs/${region}/${account_id}/${year}/${month}/${day}/${hour}/',
  'classification'='json', 
  'compressionType'='gzip', 
  'partition_filtering.enabled'='true', 
  'typeOfData'='file')