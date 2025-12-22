QS Vended Log

Put delivery source

~ $ aws logs put-delivery-source —name qs-chat-log —resource-arn arn:aws:quicksight:us-east-1:905178920046:account/905178920046 —log-type CHAT_LOGS —region us-east-1
{
"deliverySource": {
"name": "qs-chat-log",
"arn": "arn:aws:logs:us-east-1:905178920046:delivery-source:qs-chat-log",
"resourceArns": [
"arn:aws:quicksight:us-east-1:905178920046:account/905178920046"
],
"service": "quicksight",
"logType": "CHAT_LOGS"
}
}
~ $ aws logs put-delivery-source —name qs-feedback-log —resource-arn arn:aws:quicksight:us-east-1:905178920046:account/905178920046 —log-type FEEDBACK_LOGS —region us-east-1

{
"deliverySource": {
"name": "qs-feedback-log",
"arn": "arn:aws:logs:us-east-1:905178920046:delivery-source:qs-feedback-log",
"resourceArns": [
"arn:aws:quicksight:us-east-1:905178920046:account/905178920046"
],
"service": "quicksight",
"logType": "FEEDBACK_LOGS"
}
}

CW log group

aws logs create-log-group --log-group-name qs-chat-log-group --region us-east-1

aws logs create-log-group --log-group-name qs-feedback-log-group --region us-east-1

aws logs describe-log-groups --log-group-name-prefix qs-chat-log-group --region us-east-1
{
"logGroups": [
{
"logGroupName": "qs-chat-log-group",
"creationTime": 1766003075048,
"metricFilterCount": 0,
"arn": "arn:aws:logs:us-east-1:905178920046:log-group:qs-chat-log-group:*",
"storedBytes": 0,
"logGroupClass": "STANDARD",
"logGroupArn": "arn:aws:logs:us-east-1:905178920046:log-group:qs-chat-log-group",
"deletionProtectionEnabled": false
}
]
}

~ $ aws logs describe-log-groups —log-group-name-prefix qs-feedback-log-group —region us-east-1
{
"logGroups": [
{
"logGroupName": "qs-feedback-log-group",
"creationTime": 1766003100524,
"metricFilterCount": 0,
"arn": "arn:aws:logs:us-east-1:905178920046:log-group:qs-feedback-log-group:*",
"storedBytes": 0,
"logGroupClass": "STANDARD",
"logGroupArn": "arn:aws:logs:us-east-1:905178920046:log-group:qs-feedback-log-group",
"deletionProtectionEnabled": false
}
]
}


CW log destination



S3 log destination

aws logs put-delivery-destination --name qs-chat-log-s3 --delivery-destination-type S3 --delivery-destination-configuration destinationResourceArn=arn:aws:s3:::admin-console-new-905178920046/monitoring/quicksight/cw-vended-log/chat-log/ --region us-east-1

{
    "deliveryDestination": {
        "name": "qs-chat-log-s3",
        "arn": "arn:aws:logs:us-east-1:905178920046:delivery-destination:qs-chat-log-s3",
        "deliveryDestinationType": "S3",
        "deliveryDestinationConfiguration": {
            "destinationResourceArn": "arn:aws:s3:::admin-console-new-905178920046/monitoring/quicksight/cw-vended-log/chat-log/"
        }
    }
}


aws logs put-delivery-destination --name qs-feedback-log-s3 --delivery-destination-type S3 --delivery-destination-configuration destinationResourceArn=arn:aws:s3:::admin-console-new-905178920046/monitoring/quicksight/cw-vended-log/feedback-log/ --region us-east-1

{
    "deliveryDestination": {
        "name": "qs-feedback-log-s3",
        "arn": "arn:aws:logs:us-east-1:905178920046:delivery-destination:qs-feedback-log-s3",
        "deliveryDestinationType": "S3",
        "deliveryDestinationConfiguration": {
            "destinationResourceArn": "arn:aws:s3:::admin-console-new-905178920046/monitoring/quicksight/cw-vended-log/feedback-log/"
        }
    }
}

Create delivery



aws logs create-delivery --delivery-source-name qs-chat-log --delivery-destination-arn arn:aws:logs:us-east-1:905178920046:delivery-destination:qs-chat-log-s3 --region us-east-1

{
    "delivery": {
        "id": "62tZFLZGKMkoqZX8",
        "arn": "arn:aws:logs:us-east-1:905178920046:delivery:62tZFLZGKMkoqZX8",
        "deliverySourceName": "qs-chat-log",
        "deliveryDestinationArn": "arn:aws:logs:us-east-1:905178920046:delivery-destination:qs-chat-log-s3",
        "deliveryDestinationType": "S3",
        "recordFields": [
            "resource_arn",
            "event_timestamp",
            "logType",
            "accountId",
            "user_arn",
            "user_type",
            "status_code",
            "conversation_id",
            "system_message_id",
            "message_scope",
            "user_message_id",
            "user_message",
            "agent_id",
            "flow_id",
            "system_text_message",
            "user_selected_resources",
            "action_connectors",
            "cited_resource",
            "file_attachment"
        ],
        "s3DeliveryConfiguration": {
            "suffixPath": "{region}/{yyyy}/{MM}/{dd}/{HH}/",
            "enableHiveCompatiblePath": false
        }
    }
}





aws logs create-delivery --delivery-source-name qs-feedback-log --delivery-destination-arn arn:aws:logs:us-east-1:905178920046:delivery-destination:qs-feedback-log-s3 --region us-east-1


{
"delivery": {
"id": "3jdmLu3XwD60gmRt",
"arn": "arn:aws:logs:us-east-1:905178920046:delivery:3jdmLu3XwD60gmRt",
"deliverySourceName": "qs-feedback-log",
"deliveryDestinationArn": "arn:aws:logs:us-east-1:905178920046:delivery-destination:qs-feedback-log-s3",
"deliveryDestinationType": "S3",
"recordFields": [
"resource_arn",
"event_timestamp",
"logType",
"accountId",
"user_arn",
"user_type",
"status_code",
"conversation_id",
"research_id",
"system_message_id",
"user_message_id",
"feedback_type",
"feedback_reason",
"rating"
],
"s3DeliveryConfiguration": {
"suffixPath": "{region}/{yyyy}/{MM}/{dd}/{HH}/",
"enableHiveCompatiblePath": false
}
}
}

