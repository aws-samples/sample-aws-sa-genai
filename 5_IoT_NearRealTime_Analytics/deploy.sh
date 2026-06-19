#!/usr/bin/env bash
# =============================================================================
# IoT Near Real-Time Analytics Pipeline — Deployment Script
#
# Architecture:
#   Lambda Simulator → Kinesis Data Streams → Firehose → S3 Tables (telemetry)
#                                                                 ↓
#                              EventBridge (hourly) → Lambda ELT → S3 Tables (measurements)
#
# Static tables (organizations, clients, farms, fields, machines, machine_tags,
#   scuds, histogram, field_operation_products) are loaded to a regular S3 bucket
#   and registered as Athena external tables in the same iot_analytics database.
#
# Usage:
#   cp config.env.template config.env
#   # Edit config.env with your account ID and settings
#   source config.env
#   bash deploy.sh [--step N]   # run all steps, or a specific step 1-7
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- Load config ----
CONFIG_FILE="${SCRIPT_DIR}/config.env"
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: config.env not found. Copy config.env.template to config.env and fill in your values."
  exit 1
fi
source "$CONFIG_FILE"

# Export AWS_PROFILE so all aws CLI calls pick it up automatically
export AWS_PROFILE="${AWS_PROFILE:-default}"
export AWS_DEFAULT_REGION="${AWS_REGION}"
echo "Using AWS profile: $AWS_PROFILE  |  Region: $AWS_REGION  |  Account: $ACCOUNT_ID"

# Config values are expected to be literal (already have account ID substituted).

STEP_FILTER="${2:-all}"
[[ "${1:-}" == "--step" ]] && STEP_FILTER="$2"

log() { echo -e "\n\033[1;34m▶ $*\033[0m"; }
ok()  { echo -e "\033[1;32m  ✓ $*\033[0m"; }
warn(){ echo -e "\033[1;33m  ⚠ $*\033[0m"; }

should_run() { [[ "$STEP_FILTER" == "all" || "$STEP_FILTER" == "$1" ]]; }

# =============================================================================
# STEP 1 — IAM Roles
# =============================================================================
if should_run 1; then
log "STEP 1: Creating IAM roles"

# --- Firehose role ---
# Trust policy: firehose.amazonaws.com with ExternalId = account ID
cat > /tmp/firehose-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "firehose.amazonaws.com" },
      "Action": "sts:AssumeRole",
      "Condition": { "StringEquals": { "sts:ExternalId": "${ACCOUNT_ID}" } }
    }
  ]
}
EOF

aws iam create-role \
  --role-name "$FIREHOSE_ROLE_NAME" \
  --assume-role-policy-document file:///tmp/firehose-trust-policy.json \
  --region "$AWS_REGION" 2>/dev/null || warn "Role $FIREHOSE_ROLE_NAME already exists, skipping creation"

STREAM_ARN="arn:aws:kinesis:${AWS_REGION}:${ACCOUNT_ID}:stream/${KINESIS_STREAM_NAME}"
TABLE_BUCKET_ARN="arn:aws:s3tables:${AWS_REGION}:${ACCOUNT_ID}:bucket/${TABLE_BUCKET_NAME}"

cat > /tmp/firehose-permissions.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3TablesAccess",
      "Effect": "Allow",
      "Action": [
        "s3tables:GetTable",
        "s3tables:GetTableMetadataLocation",
        "s3tables:UpdateTableMetadataLocation",
        "s3tables:GetTableBucket",
        "s3tables:PutTableData",
        "s3tables:GetTableData"
      ],
      "Resource": [
        "${TABLE_BUCKET_ARN}",
        "${TABLE_BUCKET_ARN}/table/*"
      ]
    },
    {
      "Sid": "GlueCatalogAccess",
      "Effect": "Allow",
      "Action": [
        "glue:GetTable",
        "glue:GetDatabase",
        "glue:UpdateTable"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LakeFormationAccess",
      "Effect": "Allow",
      "Action": ["lakeformation:GetDataAccess"],
      "Resource": "*"
    },
    {
      "Sid": "KinesisRead",
      "Effect": "Allow",
      "Action": [
        "kinesis:DescribeStream",
        "kinesis:GetShardIterator",
        "kinesis:GetRecords",
        "kinesis:ListShards"
      ],
      "Resource": "${STREAM_ARN}"
    },
    {
      "Sid": "S3ErrorBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:AbortMultipartUpload"
      ],
      "Resource": [
        "arn:aws:s3:::${FIREHOSE_ERROR_BUCKET}",
        "arn:aws:s3:::${FIREHOSE_ERROR_BUCKET}/*"
      ]
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": ["logs:PutLogEvents", "logs:CreateLogStream", "logs:CreateLogGroup"],
      "Resource": "arn:aws:logs:${AWS_REGION}:${ACCOUNT_ID}:log-group:/aws/firehose/${FIREHOSE_STREAM_NAME}:*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name "$FIREHOSE_ROLE_NAME" \
  --policy-name "FirehoseDeliveryPolicy" \
  --policy-document file:///tmp/firehose-permissions.json
ok "Firehose role configured: $FIREHOSE_ROLE_NAME"

# --- Lambda role ---
aws iam create-role \
  --role-name "$LAMBDA_ROLE_NAME" \
  --assume-role-policy-document file://"${SCRIPT_DIR}/iam/lambda-trust.json" \
  --region "$AWS_REGION" 2>/dev/null || warn "Role $LAMBDA_ROLE_NAME already exists, skipping creation"

cat > /tmp/lambda-permissions.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "KinesisWrite",
      "Effect": "Allow",
      "Action": ["kinesis:PutRecord", "kinesis:PutRecords"],
      "Resource": "${STREAM_ARN}"
    },
    {
      "Sid": "AthenaAccess",
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StopQueryExecution"
      ],
      "Resource": "arn:aws:athena:${AWS_REGION}:${ACCOUNT_ID}:workgroup/primary"
    },
    {
      "Sid": "S3QueryOutput",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:GetBucketLocation", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::${ATHENA_OUTPUT_BUCKET}",
        "arn:aws:s3:::${ATHENA_OUTPUT_BUCKET}/*"
      ]
    },
    {
      "Sid": "IcebergReadWrite",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetBucketLocation",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${ICEBERG_BUCKET}",
        "arn:aws:s3:::${ICEBERG_BUCKET}/*"
      ]
    },
    {
      "Sid": "LakeFormationAccess",
      "Effect": "Allow",
      "Action": ["lakeformation:GetDataAccess"],
      "Resource": "*"
    },
    {
      "Sid": "GlueAccess",
      "Effect": "Allow",
      "Action": ["glue:GetTable", "glue:GetDatabase", "glue:GetPartitions", "glue:UpdateTable"],
      "Resource": [
        "arn:aws:glue:${AWS_REGION}:${ACCOUNT_ID}:catalog",
        "arn:aws:glue:${AWS_REGION}:${ACCOUNT_ID}:database/${NAMESPACE}",
        "arn:aws:glue:${AWS_REGION}:${ACCOUNT_ID}:table/${NAMESPACE}/*"
      ]
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:${AWS_REGION}:${ACCOUNT_ID}:log-group:/aws/lambda/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-name "IoTLambdaPolicy" \
  --policy-document file:///tmp/lambda-permissions.json
ok "Lambda role configured: $LAMBDA_ROLE_NAME"

# Trust policy for Firehose needs the account ID substituted
sed "s/ACCOUNT_ID_PLACEHOLDER/$ACCOUNT_ID/g" \
  "${SCRIPT_DIR}/iam/firehose-trust.json" > /tmp/firehose-trust-final.json
aws iam update-assume-role-policy \
  --role-name "$FIREHOSE_ROLE_NAME" \
  --policy-document file:///tmp/firehose-trust-final.json
fi

# =============================================================================
# STEP 2 — Kinesis Data Stream
# =============================================================================
if should_run 2; then
log "STEP 2: Creating Kinesis Data Stream"

aws kinesis create-stream \
  --stream-name "$KINESIS_STREAM_NAME" \
  --stream-mode-details StreamMode=ON_DEMAND \
  --region "$AWS_REGION" 2>/dev/null || warn "Stream $KINESIS_STREAM_NAME already exists"

echo "Waiting for stream to become ACTIVE..."
aws kinesis wait stream-exists --stream-name "$KINESIS_STREAM_NAME" --region "$AWS_REGION"

STREAM_STATUS=$(aws kinesis describe-stream-summary \
  --stream-name "$KINESIS_STREAM_NAME" \
  --region "$AWS_REGION" \
  --query "StreamDescriptionSummary.StreamStatus" \
  --output text)
ok "Stream status: $STREAM_STATUS"

STREAM_ARN=$(aws kinesis describe-stream-summary \
  --stream-name "$KINESIS_STREAM_NAME" \
  --region "$AWS_REGION" \
  --query "StreamDescriptionSummary.StreamARN" \
  --output text)
ok "Stream ARN: $STREAM_ARN"
fi

# =============================================================================
# STEP 3 — S3 Buckets (static data + Athena results)
# =============================================================================
if should_run 3; then
log "STEP 3: Creating S3 buckets"

for BUCKET in "$STATIC_DATA_BUCKET" "$ATHENA_OUTPUT_BUCKET" "$ICEBERG_BUCKET" "$FIREHOSE_ERROR_BUCKET"; do
  if [[ "$AWS_REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" 2>/dev/null || warn "Bucket $BUCKET already exists"
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" \
      --create-bucket-configuration LocationConstraint="$AWS_REGION" 2>/dev/null || warn "Bucket $BUCKET already exists"
  fi
  ok "Bucket ready: s3://$BUCKET"
done

# Create the Glue database that will hold all tables
aws glue create-database \
  --database-input "{\"Name\":\"${NAMESPACE}\",\"Description\":\"IoT analytics — telemetry + reference tables\"}" \
  --region "$AWS_REGION" 2>/dev/null || warn "Glue database ${NAMESPACE} already exists"
ok "Glue database ready: $NAMESPACE"
fi

# =============================================================================
# STEP 4 — S3 Table Bucket, Namespace, and Tables
# =============================================================================
if should_run 4; then
log "STEP 4: Creating S3 Table Bucket, namespace, and Iceberg tables"

# Create table bucket
aws s3tables create-table-bucket \
  --region "$AWS_REGION" \
  --name "$TABLE_BUCKET_NAME" 2>/dev/null || warn "Table bucket $TABLE_BUCKET_NAME already exists"

TABLE_BUCKET_ARN="arn:aws:s3tables:${AWS_REGION}:${ACCOUNT_ID}:bucket/${TABLE_BUCKET_NAME}"
ok "Table Bucket ARN: $TABLE_BUCKET_ARN"

# Create namespace
aws s3tables create-namespace \
  --table-bucket-arn "$TABLE_BUCKET_ARN" \
  --namespace "$NAMESPACE" \
  --region "$AWS_REGION" 2>/dev/null || warn "Namespace $NAMESPACE already exists"
ok "Namespace: $NAMESPACE"

# Create telemetry managed Iceberg table
aws s3tables create-table \
  --region "$AWS_REGION" \
  --table-bucket-arn "$TABLE_BUCKET_ARN" \
  --namespace "$NAMESPACE" \
  --name telemetry \
  --format ICEBERG \
  --metadata '{"iceberg":{"schema":{"fields":[{"name":"device_id","type":"string"},{"name":"organization_id","type":"string"},{"name":"event_time","type":"timestamp"},{"name":"ingest_time","type":"timestamp"},{"name":"machine_status","type":"string"},{"name":"autotrac_active","type":"boolean"},{"name":"section_control_on","type":"boolean"},{"name":"autopath_on","type":"boolean"},{"name":"fieldcruise_on","type":"boolean"},{"name":"ipm_on","type":"boolean"},{"name":"mfwd_on","type":"boolean"},{"name":"rear_pto_on","type":"boolean"},{"name":"wheel_slip_pct","type":"double"},{"name":"sample_interval_sec","type":"int"}]}}}' \
  2>/dev/null || warn "Table telemetry already exists"
ok "Telemetry table created"

# Resource policy: allows Glue service to perform S3 Tables operations (required for Firehose)
aws s3tables put-table-bucket-policy \
  --region "$AWS_REGION" \
  --table-bucket-arn "$TABLE_BUCKET_ARN" \
  --resource-policy "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{
      \"Sid\": \"AllowGlueCatalogIntegration\",
      \"Effect\": \"Allow\",
      \"Principal\": { \"Service\": \"glue.amazonaws.com\" },
      \"Action\": [
        \"s3tables:GetTable\",
        \"s3tables:GetTableMetadataLocation\",
        \"s3tables:GetTableData\",
        \"s3tables:PutTableData\",
        \"s3tables:UpdateTableMetadataLocation\"
      ],
      \"Resource\": \"${TABLE_BUCKET_ARN}/table/*\"
    }]
  }" 2>/dev/null || warn "Table bucket policy already set"
ok "Table bucket resource policy applied"

# Lake Formation: grant IAM_ALLOWED_PRINCIPALS ALL so IAM is the effective gatekeeper
# (S3 Tables auto-registers with LF; without this, all LF checks are denied by default)
aws lakeformation grant-permissions \
  --catalog-id "$ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --principal "DataLakePrincipalIdentifier=IAM_ALLOWED_PRINCIPALS" \
  --resource "{\"Database\":{\"CatalogId\":\"${ACCOUNT_ID}:s3tablescatalog/${TABLE_BUCKET_NAME}\",\"Name\":\"${NAMESPACE}\"}}" \
  --permissions "ALL" 2>/dev/null || warn "LF database grant already exists"

aws lakeformation grant-permissions \
  --catalog-id "$ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --principal "DataLakePrincipalIdentifier=IAM_ALLOWED_PRINCIPALS" \
  --resource "{\"Table\":{\"CatalogId\":\"${ACCOUNT_ID}:s3tablescatalog/${TABLE_BUCKET_NAME}\",\"DatabaseName\":\"${NAMESPACE}\",\"Name\":\"telemetry\"}}" \
  --permissions "ALL" 2>/dev/null || warn "LF table grant already exists"
ok "Lake Formation IAM pass-through grants applied"
fi

# =============================================================================
# STEP 5 — Athena: Apply Schema DDL
# =============================================================================
if should_run 5; then
log "STEP 5: Applying table schemas via Athena"

TABLE_BUCKET_ARN="arn:aws:s3tables:${AWS_REGION}:${ACCOUNT_ID}:bucket/${TABLE_BUCKET_NAME}"

run_athena() {
  local SQL="$1"
  local EXEC_ID
  EXEC_ID=$(aws athena start-query-execution \
    --query-string "$SQL" \
    --result-configuration "OutputLocation=s3://${ATHENA_OUTPUT_BUCKET}/athena-results/" \
    --region "$AWS_REGION" \
    --query "QueryExecutionId" \
    --output text)
  echo "  Query ID: $EXEC_ID"
  for i in $(seq 1 30); do
    STATUS=$(aws athena get-query-execution \
      --query-execution-id "$EXEC_ID" \
      --region "$AWS_REGION" \
      --query "QueryExecution.Status.State" \
      --output text)
    [[ "$STATUS" == "SUCCEEDED" ]] && return 0
    [[ "$STATUS" == "FAILED" || "$STATUS" == "CANCELLED" ]] && {
      REASON=$(aws athena get-query-execution --query-execution-id "$EXEC_ID" \
        --region "$AWS_REGION" --query "QueryExecution.Status.StateChangeReason" --output text)
      echo "  FAILED: $REASON"
      return 1
    }
    sleep 3
  done
  echo "  Query timed out"
  return 1
}

# telemetry DDL
TELEMETRY_DDL=$(cat "${SCRIPT_DIR}/sql/01_create_telemetry_table.sql" \
  | sed "s|NAMESPACE_PLACEHOLDER|${NAMESPACE}|g" \
  | sed "s|ICEBERG_BUCKET_PLACEHOLDER|${ICEBERG_BUCKET}|g")

echo "  Applying telemetry schema..."
run_athena "$TELEMETRY_DDL" && ok "telemetry table schema applied" || warn "telemetry DDL failed — check error above"

# measurements DDL
MEASUREMENTS_DDL=$(cat "${SCRIPT_DIR}/sql/02_create_measurements_table.sql" \
  | sed "s|NAMESPACE_PLACEHOLDER|${NAMESPACE}|g" \
  | sed "s|ICEBERG_BUCKET_PLACEHOLDER|${ICEBERG_BUCKET}|g")

echo "  Applying measurements schema..."
run_athena "$MEASUREMENTS_DDL" && ok "measurements table schema applied" || warn "measurements DDL failed — check error above"

# Static reference table DDLs
echo "  Registering static reference tables..."
while IFS= read -r SQL_FILE; do
  TABLE_NAME=$(basename "$SQL_FILE" .sql)
  SQL=$(cat "$SQL_FILE" \
    | sed "s|NAMESPACE_PLACEHOLDER|${NAMESPACE}|g" \
    | sed "s|STATIC_DATA_BUCKET_PLACEHOLDER|${STATIC_DATA_BUCKET}|g")
  echo "  Applying schema for: $TABLE_NAME"
  run_athena "$SQL" && ok "$TABLE_NAME external table registered"
done < <(find "${SCRIPT_DIR}/sql/static_tables" -name "*.sql" 2>/dev/null | sort)
fi

# =============================================================================
# STEP 6 — Load Static Reference Data to S3
# =============================================================================
if should_run 6; then
log "STEP 6: Uploading static CSV data to S3"

DEMO_DATA_DIR="${SCRIPT_DIR}/../demo_data"

for TABLE in organizations clients farms fields machines machine_tags scuds histogram field_operation_products; do
  CSV_FILE="${DEMO_DATA_DIR}/${TABLE}.csv"
  if [[ -f "$CSV_FILE" ]]; then
    aws s3 cp "$CSV_FILE" "s3://${STATIC_DATA_BUCKET}/static/${TABLE}/${TABLE}.csv" \
      --region "$AWS_REGION"
    ok "Uploaded: ${TABLE}.csv"
  else
    warn "CSV not found: $CSV_FILE"
  fi
done
fi

# =============================================================================
# STEP 7 — Amazon Data Firehose
# =============================================================================
if should_run 7; then
log "STEP 7: Creating Firehose delivery stream"

STREAM_ARN=$(aws kinesis describe-stream-summary \
  --stream-name "$KINESIS_STREAM_NAME" \
  --region "$AWS_REGION" \
  --query "StreamDescriptionSummary.StreamARN" \
  --output text)

TABLE_BUCKET_ARN="arn:aws:s3tables:${AWS_REGION}:${ACCOUNT_ID}:bucket/${TABLE_BUCKET_NAME}"

FIREHOSE_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${FIREHOSE_ROLE_NAME}"
# CatalogARN must point to the S3 Tables sub-catalog for this table bucket
GLUE_CATALOG_ARN="arn:aws:glue:${AWS_REGION}:${ACCOUNT_ID}:catalog/s3tablescatalog/${TABLE_BUCKET_NAME}"

cat > /tmp/firehose-config.json << EOF
{
  "DeliveryStreamName": "${FIREHOSE_STREAM_NAME}",
  "DeliveryStreamType": "KinesisStreamAsSource",
  "KinesisStreamSourceConfiguration": {
    "KinesisStreamARN": "${STREAM_ARN}",
    "RoleARN": "${FIREHOSE_ROLE_ARN}"
  },
  "IcebergDestinationConfiguration": {
    "RoleARN": "${FIREHOSE_ROLE_ARN}",
    "CatalogConfiguration": {
      "CatalogARN": "${GLUE_CATALOG_ARN}"
    },
    "S3Configuration": {
      "BucketARN": "arn:aws:s3:::${FIREHOSE_ERROR_BUCKET}",
      "RoleARN": "${FIREHOSE_ROLE_ARN}",
      "ErrorOutputPrefix": "firehose-errors/"
    },
    "DestinationTableConfigurationList": [
      {
        "DestinationTableName": "telemetry",
        "DestinationDatabaseName": "${NAMESPACE}",
        "UniqueKeys": ["device_id", "event_time"]
      }
    ],
    "BufferingHints": {
      "SizeInMBs": 128,
      "IntervalInSeconds": 60
    },
    "CloudWatchLoggingOptions": {
      "Enabled": true,
      "LogGroupName": "/aws/firehose/${FIREHOSE_STREAM_NAME}",
      "LogStreamName": "DestinationDelivery"
    }
  }
}
EOF

aws firehose create-delivery-stream \
  --cli-input-json file:///tmp/firehose-config.json \
  --region "$AWS_REGION" 2>/dev/null || warn "Firehose stream already exists"

echo "Waiting for Firehose to become ACTIVE (~2 minutes)..."
for i in $(seq 1 24); do
  STATUS=$(aws firehose describe-delivery-stream \
    --delivery-stream-name "$FIREHOSE_STREAM_NAME" \
    --region "$AWS_REGION" \
    --query "DeliveryStreamDescription.DeliveryStreamStatus" \
    --output text 2>/dev/null || echo "CREATING")
  [[ "$STATUS" == "ACTIVE" ]] && break
  echo "  Status: $STATUS (${i}/24)"
  sleep 5
done
ok "Firehose status: ACTIVE"
fi

# =============================================================================
# STEP 8 — Lambda Functions
# =============================================================================
if should_run 8; then
log "STEP 8: Deploying Lambda functions"

LAMBDA_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${LAMBDA_ROLE_NAME}"

# Wait for IAM role to propagate
sleep 10

# --- Simulator Lambda ---
echo "  Packaging simulator Lambda..."
SIM_DIR="${SCRIPT_DIR}/lambda/simulator"
rm -rf "${SIM_DIR}/package"
mkdir -p "${SIM_DIR}/package"
pip install -r "${SIM_DIR}/requirements.txt" -t "${SIM_DIR}/package/" -q 2>/dev/null || true
cp "${SIM_DIR}/handler.py" "${SIM_DIR}/package/"
(cd "${SIM_DIR}/package" && zip -r /tmp/simulator.zip . -q)
rm -rf "${SIM_DIR}/package"

aws lambda create-function \
  --function-name "$SIMULATOR_LAMBDA" \
  --runtime python3.12 \
  --role "$LAMBDA_ROLE_ARN" \
  --handler handler.lambda_handler \
  --zip-file fileb:///tmp/simulator.zip \
  --timeout 60 \
  --memory-size 256 \
  --environment "Variables={KINESIS_STREAM_NAME=${KINESIS_STREAM_NAME},AWS_REGION_NAME=${AWS_REGION}}" \
  --region "$AWS_REGION" 2>/dev/null || \
aws lambda update-function-code \
  --function-name "$SIMULATOR_LAMBDA" \
  --zip-file fileb:///tmp/simulator.zip \
  --region "$AWS_REGION"
ok "Simulator Lambda deployed: $SIMULATOR_LAMBDA"

# --- ELT Lambda ---
echo "  Packaging ELT Lambda..."
ELT_DIR="${SCRIPT_DIR}/lambda/elt_processor"
rm -rf "${ELT_DIR}/package"
mkdir -p "${ELT_DIR}/package"
pip install -r "${ELT_DIR}/requirements.txt" -t "${ELT_DIR}/package/" -q 2>/dev/null || true
cp "${ELT_DIR}/handler.py" "${ELT_DIR}/package/"
(cd "${ELT_DIR}/package" && zip -r /tmp/elt.zip . -q)
rm -rf "${ELT_DIR}/package"

aws lambda create-function \
  --function-name "$ELT_LAMBDA" \
  --runtime python3.12 \
  --role "$LAMBDA_ROLE_ARN" \
  --handler handler.lambda_handler \
  --zip-file fileb:///tmp/elt.zip \
  --timeout 300 \
  --memory-size 256 \
  --environment "Variables={ATHENA_DB=${NAMESPACE},ATHENA_OUTPUT_BUCKET=${ATHENA_OUTPUT_BUCKET},AWS_REGION_NAME=${AWS_REGION}}" \
  --region "$AWS_REGION" 2>/dev/null || \
aws lambda update-function-code \
  --function-name "$ELT_LAMBDA" \
  --zip-file fileb:///tmp/elt.zip \
  --region "$AWS_REGION"
ok "ELT Lambda deployed: $ELT_LAMBDA"

# --- EventBridge rules ---
echo "  Creating EventBridge schedule for simulator (every 1 minute)..."
SIMULATOR_RULE_ARN=$(aws events put-rule \
  --name "iot-simulator-schedule" \
  --schedule-expression "$SIMULATOR_SCHEDULE" \
  --state ENABLED \
  --region "$AWS_REGION" \
  --query "RuleArn" --output text)

SIMULATOR_LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:${SIMULATOR_LAMBDA}"
aws lambda add-permission \
  --function-name "$SIMULATOR_LAMBDA" \
  --statement-id "EventBridgeInvoke-simulator" \
  --action "lambda:InvokeFunction" \
  --principal "events.amazonaws.com" \
  --source-arn "$SIMULATOR_RULE_ARN" \
  --region "$AWS_REGION" 2>/dev/null || true

aws events put-targets \
  --rule "iot-simulator-schedule" \
  --targets "Id=SimulatorTarget,Arn=${SIMULATOR_LAMBDA_ARN}" \
  --region "$AWS_REGION"
ok "Simulator scheduled: $SIMULATOR_SCHEDULE"

echo "  Creating EventBridge schedule for ELT (hourly)..."
ELT_RULE_ARN=$(aws events put-rule \
  --name "iot-elt-schedule" \
  --schedule-expression "$ELT_SCHEDULE" \
  --state ENABLED \
  --region "$AWS_REGION" \
  --query "RuleArn" --output text)

ELT_LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:${ELT_LAMBDA}"
aws lambda add-permission \
  --function-name "$ELT_LAMBDA" \
  --statement-id "EventBridgeInvoke-elt" \
  --action "lambda:InvokeFunction" \
  --principal "events.amazonaws.com" \
  --source-arn "$ELT_RULE_ARN" \
  --region "$AWS_REGION" 2>/dev/null || true

aws events put-targets \
  --rule "iot-elt-schedule" \
  --targets "Id=ELTTarget,Arn=${ELT_LAMBDA_ARN}" \
  --region "$AWS_REGION"
ok "ELT scheduled: $ELT_SCHEDULE"
fi

# =============================================================================
# Done
# =============================================================================
log "Deployment complete!"
echo ""
echo "  Kinesis Stream  : $KINESIS_STREAM_NAME"
echo "  Firehose Stream : $FIREHOSE_STREAM_NAME"
echo "  S3 Table Bucket : $TABLE_BUCKET_NAME"
echo "  Database        : $NAMESPACE"
echo "  Tables (live)   : telemetry, measurements"
echo "  Simulator Lambda: $SIMULATOR_LAMBDA  (runs every 1 min)"
echo "  ELT Lambda      : $ELT_LAMBDA        (runs hourly)"
echo ""
echo "Next steps:"
echo "  1. Wait ~90 seconds for first telemetry records to appear in S3 Tables"
echo "  2. Query: SELECT COUNT(*) FROM ${NAMESPACE}.telemetry"
echo "  3. After 1 hour: SELECT COUNT(*) FROM ${NAMESPACE}.measurements"
echo "  4. Connect QuickSight to the ${NAMESPACE} database in Glue Data Catalog"
