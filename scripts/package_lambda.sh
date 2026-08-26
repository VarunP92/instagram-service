#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
ZIP_PATH="${BUILD_DIR}/lambda.zip"

echo "==> Packaging Lambda source into ${ZIP_PATH}"

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

cd "${ROOT_DIR}"
zip -r -q "${ZIP_PATH}" src -x "*/_pycache_/*"

echo "==> Package created: ${ZIP_PATH}"
