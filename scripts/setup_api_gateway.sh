#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

lambda_arn() {
  awscli lambda get-function \
    --function-name "$1" \
    --query 'Configuration.FunctionArn' \
    --output text
}

echo "==> Looking for existing REST API named '${API_NAME}'"

API_ID=$(awscli apigateway get-rest-apis \
  --query "items[?name=='${API_NAME}'].id" \
  --output text)

if [ -z "${API_ID}" ] || [ "${API_ID}" == "None" ]; then
  echo "==> Creating REST API: ${API_NAME}"
  API_ID=$(awscli apigateway create-rest-api \
    --name "${API_NAME}" \
    --query 'id' \
    --output text)
else
  echo "    Found existing API: ${API_ID}"
fi

ROOT_ID=$(awscli apigateway get-resources \
  --rest-api-id "${API_ID}" \
  --query "items[?path=='/'].id" \
  --output text)

get_or_create_resource() {
  local parent_id="$1"
  local path_part="$2"
  local existing

  existing=$(awscli apigateway get-resources \
    --rest-api-id "${API_ID}" \
    --query "items[?pathPart=='${path_part}' && parentId=='${parent_id}'].id" \
    --output text)

  if [ -n "${existing}" ] && [ "${existing}" != "None" ]; then
    echo "${existing}"
  else
    awscli apigateway create-resource \
      --rest-api-id "${API_ID}" \
      --parent-id "${parent_id}" \
      --path-part "${path_part}" \
      --query 'id' \
      --output text
  fi
}

IMAGES_RESOURCE_ID=$(get_or_create_resource "${ROOT_ID}" "images")
IMAGE_ID_RESOURCE_ID=$(get_or_create_resource "${IMAGES_RESOURCE_ID}" "{image_id}")

add_method() {
  local resource_id="$1"
  local http_method="$2"
  local function_name="$3"
  local arn
  arn=$(lambda_arn "${function_name}")

  local uri="arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${arn}/invocations"

  echo "==> Wiring ${http_method} on resource ${resource_id} -> ${function_name}"

  awscli apigateway put-method \
    --rest-api-id "${API_ID}" \
    --resource-id "${resource_id}" \
    --http-method "${http_method}" \
    --authorization-type "NONE" >/dev/null 2>&1 || true

  awscli apigateway put-integration \
    --rest-api-id "${API_ID}" \
    --resource-id "${resource_id}" \
    --http-method "${http_method}" \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "${uri}" >/dev/null 2>&1 || true

  awscli lambda add-permission \
    --function-name "${function_name}" \
    --statement-id "apigw-${function_name}-${http_method}" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${AWS_REGION}:000000000000:${API_ID}//" \
    >/dev/null 2>&1 || true
}

add_method "${IMAGES_RESOURCE_ID}" "POST" "images-upload"
add_method "${IMAGES_RESOURCE_ID}" "GET" "images-list"
add_method "${IMAGE_ID_RESOURCE_ID}" "GET" "images-get"
add_method "${IMAGE_ID_RESOURCE_ID}" "DELETE" "images-delete"

echo "==> Creating deployment (stage: ${API_STAGE})"

awscli apigateway create-deployment \
  --rest-api-id "${API_ID}" \
  --stage-name "${API_STAGE}" >/dev/null

BASE_URL="http://localhost:4566/restapis/${API_ID}/${API_STAGE}/user_request"

echo ""
echo "============================================================"
echo "==> API ready, Base URL:"
echo "    ${BASE_URL}"
echo ""
echo "    Endpoints:"
echo "    POST   ${BASE_URL}/images"
echo "    GET    ${BASE_URL}/images"
echo "    GET    ${BASE_URL}/images/{image_id}"
echo "    DELETE ${BASE_URL}/images/{image_id}"
echo "============================================================"

echo "${API_ID}" > "${SCRIPT_DIR}/.api_id"
