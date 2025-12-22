-- Test query with specific partition filters
SELECT COUNT(*) 
FROM qs_chat_logchat_log 
WHERE region = 'us-east-1' 
  AND year = '2025' 
  AND month = '12' 
  AND day = '17' 
  AND hour = '22'
LIMIT 10;

-- Alternative: Check if partitions exist
SHOW PARTITIONS qs_chat_logchat_log;

-- Check table location
DESCRIBE FORMATTED qs_chat_logchat_log;