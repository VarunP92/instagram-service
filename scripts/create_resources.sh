#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "==> Creating S3 bucket: ${IMAGES_BUCKET}"
awscli s3 mb "s3://${IMAGES_BUCKET}" 2>/dev/null || echo "    (bucket already exists, skipping)"

echo "==> Creating DynamoDB table: ${IMAGES_TABLE}"
if awscli dynamodb describe-table --table-name "${IMAGES_TABLE}" >/dev/null 2>&1; then
  echo "    (table already exists, skipping)"
else
  awscli dynamodb create-table \
    --table-name "${IMAGES_TABLE}" \
    --attribute-definitions \
      AttributeName=image_id,AttributeType=S \
      AttributeName=user_id,AttributeType=S \
      AttributeName=uploaded_at,AttributeType=S \
    --key-schema AttributeName=image_id,KeyType=HASH \
    --global-secondary-indexes \
    "[
      {
        \"IndexName\": \"${USER_INDEX_NAME}\",
        \"KeySchema\": [
          {\"AttributeName\": \"user_id\", \"KeyType\": \"HASH\"},
          {\"AttributeName\": \"uploaded_at\", \"KeyType\": \"RANGE\"}
        ],
        \"Projection\": {\"ProjectionType\": \"ALL\"},
        \"ProvisionedThroughput\": {\"ReadCapacityUnits\": 5, \"WriteCapacityUnits\": 5}
      }
    ]" \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --billing-mode PROVISIONED

  echo "    waiting for table to become ACTIVE..."
  awscli dynamodb wait table-exists --table-name "${IMAGES_TABLE}"
fi

echo "==> Resources ready."
