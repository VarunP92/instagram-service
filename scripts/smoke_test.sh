#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "${SCRIPT_DIR}/.api_id" ]; then
  echo "No .api_id file found -- run scripts/deploy_all.sh first."
  exit 1
fi

API_ID=$(cat "${SCRIPT_DIR}/.api_id")
BASE_URL="http://localhost:4566/restapis/${API_ID}/local/user_request"

IMG_B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mNk+A8AAQUAAQUBAScY42YAAAAASUVORK5CYII="

echo "==> 1) Upload an image"

UPLOAD_RESPONSE=$(curl -s -X POST "${BASE_URL}/images" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"demo-user\",
    \"filename\": \"pixel.png\",
    \"content_type\": \"image/png\",
    \"image_base64\": \"${IMG_B64}\",
    \"description\": \"a lone red pixel\",
    \"tags\": [\"demo\", \"pixel\"]
  }")

echo "${UPLOAD_RESPONSE}" | python -m json.tool

IMAGE_ID=$(echo "${UPLOAD_RESPONSE}" | python -c \
  "import sys,json;print(json.load(sys.stdin)['image_id'])")

echo ""

echo "==> 2) List all images"

curl -s "${BASE_URL}/images" | python -m json.tool

echo ""

echo "==> 2b) List images filtered by user_id + tag"

curl -s "${BASE_URL}/images?user_id=demo-user&tag=demo" | python -m json.tool

echo ""

echo "==> 3) Get image metadata + presigned URL"

curl -s "${BASE_URL}/images/${IMAGE_ID}" | python -m json.tool

echo ""

echo "==> 4) Delete the image"

curl -s -X DELETE \
  "${BASE_URL}/images/${IMAGE_ID}?user_id=demo-user" \
  | python -m json.tool

echo ""

echo "==> 5) Confirm it's gone (expect 404)"

curl -s -o /dev/null -w "HTTP status: %{http_code}\n" \
  "${BASE_URL}/images/${IMAGE_ID}"
