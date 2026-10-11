#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <ApiBaseUrl>"
  echo "Example: $0 https://xxxx.execute-api.ap-southeast-2.amazonaws.com/v1"
  exit 1
fi

API_BASE="${1%/}"
echo "[*] Running Argus smoke test against: $API_BASE"

# 1. Test /health
echo "[*] Testing GET /health..."
HEALTH_RESP=$(curl -sSf "${API_BASE}/health")
printf '%s\n' "$HEALTH_RESP" | python -c 'import json,sys; assert json.load(sys.stdin).get("status") == "ok"' || {
  echo "[!] Failed: /health did not return status ok."
  exit 1
}
echo "[+] /health OK."

# 2. Test /hotspots (assert >= 10)
echo "[*] Testing GET /hotspots..."
HOTSPOTS_RESP=$(curl -sSf "${API_BASE}/hotspots")
COUNT=$(printf '%s\n' "$HOTSPOTS_RESP" | python -c 'import json,sys; print(len(json.load(sys.stdin)["hotspots"]))')
if [ "$COUNT" -lt 10 ]; then
  echo "[!] Failed: /hotspots returned only $COUNT hotspots (expected >= 10)."
  exit 1
fi
echo "[+] /hotspots OK ($COUNT hotspots found)."

# 3. Test /risk?rain_3h_mm=50
echo "[*] Testing GET /risk?rain_3h_mm=50..."
RISK_RESP=$(curl -sSf "${API_BASE}/risk?rain_3h_mm=50")
RISK_COUNT=$(printf '%s\n' "$RISK_RESP" | python -c 'import json,sys; print(len(json.load(sys.stdin)["scores"]))')
if [ "$RISK_COUNT" -ne "$COUNT" ]; then
  echo "[!] Failed: /risk returned $RISK_COUNT scores, expected $COUNT."
  exit 1
fi
echo "[+] /risk OK ($RISK_COUNT scores matching hotspots)."

# 4. Test /assets
echo "[*] Testing GET /assets..."
ASSETS_RESP=$(curl -sSf "${API_BASE}/assets")
printf '%s\n' "$ASSETS_RESP" | python -c 'import json,sys; assert isinstance(json.load(sys.stdin)["assets"], list)'  || {
  echo "[!] Failed: /assets response missing 'assets' key."
  exit 1
}
echo "[+] /assets OK."

# 5. Test /eval/results
echo "[*] Testing GET /eval/results..."
EVAL_RESP=$(curl -sSf "${API_BASE}/eval/results")
printf '%s\n' "$EVAL_RESP" | python -c 'import json,sys; assert "rdd2022" in json.load(sys.stdin)'  || {
  echo "[!] Failed: /eval/results response missing expected keys."
  exit 1
}
echo "[+] /eval/results OK."

echo ""
echo "=================================================="
echo "[+] ALL SMOKE TESTS PASSED SUCCESSFULLY! (5/5)"
echo "=================================================="
