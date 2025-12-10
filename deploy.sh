#!/bin/bash
# Deploy helper to sync repo, rebuild frontend, and restart Apache.
set -euo pipefail
set -x

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$REPO_DIR"

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  SUDO=""
fi

$SUDO git pull

cd "$REPO_DIR/frontend"
$SUDO npm install

set +e
$SUDO npm run build
BUILD_STATUS=$?
set -e

# ビルドが失敗した場合はデプロイを止める
if [ $BUILD_STATUS -ne 0 ]; then
  echo "npm run build failed with status ${BUILD_STATUS}" >&2
  exit $BUILD_STATUS
fi

$SUDO systemctl restart apache2

echo "deploy finished"
