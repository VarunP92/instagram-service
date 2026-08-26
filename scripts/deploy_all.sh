#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "############################################################"
echo "## 1/4 Waiting for LocalStack to be ready"
echo "############################################################"

for i in $(seq 1 30); do
  if curl -s http://localhost:4566/_localstack/health | grep -q '"s3": "\(running\|available\)"'; then
    echo "LocalStack is up."
    break
  fi

  echo "...waiting ($i/30)"
  sleep 2
done

echo "############################################################"
echo "## 2/4 Creating S3 bucket + DynamoDB table"
echo "############################################################"

bash "${SCRIPT_DIR}/create_resources.sh"

echo "############################################################"
echo "## 3/4 Packaging + deploying Lambda functions"
echo "############################################################"

bash "${SCRIPT_DIR}/package_lambda.sh"
bash "${SCRIPT_DIR}/deploy_lambdas.sh"

echo "############################################################"
echo "## 4/4 Setting up API Gateway"
echo "############################################################"

bash "${SCRIPT_DIR}/setup_api_gateway.sh"

echo "Done!"
