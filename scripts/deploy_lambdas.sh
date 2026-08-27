#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/config.sh"

ZIP_PATH="${ROOT_DIR}/build/lambda.zip"
ZIP_PATH_WIN="$(cygpath -w "${ZIP_PATH}" 2>/dev/null || echo "${ZIP_PATH}")"

if [ ! -f "${ZIP_PATH}" ]; then
  echo "Lambda zip not found -- running package_lambda.sh first"
  "${SCRIPT_DIR}/package_lambda.sh"
fi

echo "==> Ensuring IAM execution role exists: ${LAMBDA_ROLE_NAME}"

if ! awscli iam get-role --role-name "${LAMBDA_ROLE_NAME}" >/dev/null 2>&1; then
  awscli iam create-role \
    --role-name "${LAMBDA_ROLE_NAME}" \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }' >/dev/null

  awscli iam put-role-policy \
    --role-name "${LAMBDA_ROLE_NAME}" \
    --policy-name "images-lambda-policy" \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": ["s3:", "dynamodb:", "logs:*"],
        "Resource": "*"
      }]
    }' >/dev/null
fi

ROLE_ARN="arn:aws:iam::000000000000:role/${LAMBDA_ROLE_NAME}"

declare -A HANDLERS=(
  [images-upload]="src.handlers.upload.lambda_handler"
  [images-list]="src.handlers.list_images.lambda_handler"
  [images-get]="src.handlers.get_image.lambda_handler"
  [images-delete]="src.handlers.delete_image.lambda_handler"
)

ENV_VARS="Variables={IMAGES_BUCKET=${IMAGES_BUCKET},IMAGES_TABLE=${IMAGES_TABLE},USER_INDEX_NAME=${USER_INDEX_NAME},AWS_REGION=${AWS_REGION}}"

for FUNCTION_NAME in "${!HANDLERS[@]}"; do
  HANDLER="${HANDLERS[$FUNCTION_NAME]}"

  echo "==> Deploying function: ${FUNCTION_NAME} (${HANDLER})"

  if awscli lambda get-function --function-name "${FUNCTION_NAME}" >/dev/null 2>&1; then

    awscli lambda update-function-code \
      --function-name "${FUNCTION_NAME}" \
      --zip-file "fileb://${ZIP_PATH_WIN}" >/dev/null

    awscli lambda update-function-configuration \
      --function-name "${FUNCTION_NAME}" \
      --handler "${HANDLER}" \
      --environment "${ENV_VARS}" >/dev/null

  else

    awscli lambda create-function \
      --function-name "${FUNCTION_NAME}" \
      --runtime "${LAMBDA_RUNTIME}" \
      --role "${ROLE_ARN}" \
      --handler "${HANDLER}" \
      --timeout "${LAMBDA_TIMEOUT}" \
      --memory-size "${LAMBDA_MEMORY}" \
      --zip-file "fileb://${ZIP_PATH_WIN}" \
      --environment "${ENV_VARS}" >/dev/null

  fi

  awscli lambda wait function-active \
    --function-name "${FUNCTION_NAME}" || true
done

echo "==> All Lambda functions deployed."
