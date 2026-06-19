#!/usr/bin/env bash
# Removes all resources created by deploy.sh.
# Run: source config.env && bash teardown.sh

set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.env"

export AWS_PROFILE="${AWS_PROFILE:-default}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

echo "▶ Deleting EventBridge rules..."
aws events remove-targets --rule "iot-simulator-schedule" --ids SimulatorTarget --region "$AWS_REGION" 2>/dev/null || true
aws events delete-rule --name "iot-simulator-schedule" --region "$AWS_REGION" 2>/dev/null || true
aws events remove-targets --rule "iot-elt-schedule" --ids ELTTarget --region "$AWS_REGION" 2>/dev/null || true
aws events delete-rule --name "iot-elt-schedule" --region "$AWS_REGION" 2>/dev/null || true

echo "▶ Deleting Lambda functions..."
aws lambda delete-function --function-name "$SIMULATOR_LAMBDA" --region "$AWS_REGION" 2>/dev/null || true
aws lambda delete-function --function-name "$ELT_LAMBDA" --region "$AWS_REGION" 2>/dev/null || true

echo "▶ Deleting Firehose delivery stream..."
aws firehose delete-delivery-stream --delivery-stream-name "$FIREHOSE_STREAM_NAME" --region "$AWS_REGION" 2>/dev/null || true
# Also clean up old stream name if it still exists
aws firehose delete-delivery-stream --delivery-stream-name "iot-telemetry-firehose" --region "$AWS_REGION" 2>/dev/null || true

echo "▶ Deleting Kinesis stream..."
aws kinesis delete-stream --stream-name "$KINESIS_STREAM_NAME" --region "$AWS_REGION" 2>/dev/null || true

echo "▶ Deleting S3 Tables..."
TABLE_BUCKET_ARN="arn:aws:s3tables:${AWS_REGION}:${ACCOUNT_ID}:bucket/${TABLE_BUCKET_NAME}"
if aws s3tables get-table-bucket --table-bucket-arn "$TABLE_BUCKET_ARN" --region "$AWS_REGION" &>/dev/null; then
  for TABLE in telemetry measurements; do
    aws s3tables delete-table --table-bucket-arn "$TABLE_BUCKET_ARN" \
      --namespace "$NAMESPACE" --name "$TABLE" --region "$AWS_REGION" 2>/dev/null || true
  done
  aws s3tables delete-namespace --table-bucket-arn "$TABLE_BUCKET_ARN" \
    --namespace "$NAMESPACE" --region "$AWS_REGION" 2>/dev/null || true
  aws s3tables delete-table-bucket --table-bucket-arn "$TABLE_BUCKET_ARN" \
    --region "$AWS_REGION" 2>/dev/null || true
fi

echo "▶ Emptying and deleting S3 buckets..."
for BUCKET in "$STATIC_DATA_BUCKET" "$ATHENA_OUTPUT_BUCKET" "$ICEBERG_BUCKET" "$FIREHOSE_ERROR_BUCKET"; do
  aws s3 rm "s3://$BUCKET" --recursive --region "$AWS_REGION" 2>/dev/null || true
  aws s3api delete-bucket --bucket "$BUCKET" --region "$AWS_REGION" 2>/dev/null || true
done

echo "▶ Deleting IAM roles..."
for ROLE in "$FIREHOSE_ROLE_NAME" "IoTFirehoseDeliveryRole" "$LAMBDA_ROLE_NAME"; do
  POLICIES=$(aws iam list-role-policies --role-name "$ROLE" --query "PolicyNames[]" --output text 2>/dev/null || echo "")
  for POLICY in $POLICIES; do
    aws iam delete-role-policy --role-name "$ROLE" --policy-name "$POLICY" 2>/dev/null || true
  done
  aws iam delete-role --role-name "$ROLE" 2>/dev/null || true
done

echo "✓ Teardown complete."
