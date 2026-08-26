#!/usr/bin/env bash
# Shared configuration sourced by every script in this folder.

export AWS_ENDPOINT="http://localhost:4566"
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"

export IMAGES_BUCKET="images-bucket"
export IMAGES_TABLE="images-metadata"
export USER_INDEX_NAME="user_id-index"

export LAMBDA_ROLE_NAME="images-lambda-role"
export LAMBDA_RUNTIME="python3.9"
export LAMBDA_TIMEOUT=15
export LAMBDA_MEMORY=256

export API_NAME="images-api"
export API_STAGE="local"

if command -v awslocal >/dev/null 2>&1; then
  AWS_CMD="awslocal"
else
  AWS_CMD="aws --endpoint-url=${AWS_ENDPOINT}"
fi

awscli() {
  ${AWS_CMD} --region "${AWS_REGION}" "$@"
}
