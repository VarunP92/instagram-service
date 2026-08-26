#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "==> Deleting Lambda functions"

for FUNCTION_NAME in images-upload images-list images-get images-delete; do
  awscli lambda delete-function \
    --function-name "${FUNCTION_NAME}" 2>/dev/null || true
done

if [ -f "${SCRIPT_DIR}/.api_id" ]; then
  API_ID=$(cat "${SCRIPT_DIR}/.api_id")

  echo "==> Deleting REST API ${API_ID}"

  awscli apigateway delete-rest-api \
    --rest-api-id "${API_ID}" 2>/dev/null || true

  rm -f "${SCRIPT_DIR}/.api_id"
fi

echo "==> Emptying + deleting S3 bucket ${IMAGES_BUCKET}"

awscli s3 rm "s3://${IMAGES_BUCKET}" \
  --recursive 2>/dev/null || true

awscli s3 rb "s3://${IMAGES_BUCKET}" \
  2>/dev/null || true

echo "==> Deleting DynamoDB table ${IMAGES_TABLE}"

awscli dynamodb delete-table \
  --table-name "${IMAGES_TABLE}" 2>/dev/null || true

echo "==> Teardown complete."
