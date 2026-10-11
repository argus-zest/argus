#!/usr/bin/env bash
# AWS-documented virtualenv installation; no global Python or AWS config changes.
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"
export UV_CACHE_DIR="$REPO_ROOT/.cache/uv"
export UV_HTTP_TIMEOUT=20
export UV_HTTP_RETRIES=0
command -v uv >/dev/null || { echo "uv is required for this local installer" >&2; exit 1; }
command -v python3.12 >/dev/null || { echo "Python 3.12 is required" >&2; exit 1; }
if [[ ! -x .venv-sam/bin/python ]]; then
  uv venv --python python3.12 .venv-sam
fi
uv pip install --python .venv-sam/bin/python aws-sam-cli
.venv-sam/bin/sam --version
echo 'Use: export PATH="$PWD/.venv-sam/bin:$PATH"'
