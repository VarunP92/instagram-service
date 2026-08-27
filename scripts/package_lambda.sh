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
python - <<'PY'
import shutil, os
base = os.path.join('build', 'lambda')
os.makedirs(base, exist_ok=True)
shutil.copytree('src', os.path.join(base, 'src'), ignore=shutil.ignore_patterns('_pycache_', '*.pyc'))
shutil.make_archive(os.path.join('build', 'lambda'), 'zip', base)
shutil.rmtree(base)
print('Package created')
PY

echo "==> Package created: ${ZIP_PATH}"
