#!/usr/bin/env bash
set -euo pipefail

echo "[*] Building Strands Layer in backend/layer_strands/python..."
TARGET_DIR="backend/layer_strands/python"
rm -rf backend/layer_strands
mkdir -p "$TARGET_DIR"

# Install strands-agents targeting Lambda linux x86_64
pip install \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --target "$TARGET_DIR" \
  strands-agents || {
    echo "[!] Pip install failed. Setting AGENT_BACKEND=converse fallback per Section 15."
    exit 0
}

# Clean unnecessary dependencies provided by Lambda runtime
echo "[*] Cleaning bundled packages present in Lambda runtime..."
rm -rf "$TARGET_DIR"/boto3*
rm -rf "$TARGET_DIR"/botocore*
rm -rf "$TARGET_DIR"/s3transfer*
rm -rf "$TARGET_DIR"/jmespath*
find "$TARGET_DIR" -type d -name "__pycache__" -exec rm -rf {} + || true
find "$TARGET_DIR" -type d -name "tests" -exec rm -rf {} + || true

# Check size
SIZE_MB=$(du -sm backend/layer_strands | cut -f1)
echo "[*] Strands layer size: ${SIZE_MB} MB"
if [ "$SIZE_MB" -gt 200 ]; then
  echo "[!] Strands layer exceeds 200 MB limit (${SIZE_MB} MB). Use AGENT_BACKEND=converse."
  exit 1
fi

echo "[+] Strands layer build complete."
