#!/usr/bin/env bash
set -euo pipefail

PROFILE="${AWS_PROFILE:-hackathon}"
REGION="${AWS_REGION:-ap-southeast-2}"
STACK_NAME="${STACK_NAME:-argus}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-http://localhost:5173}"
SES_FROM="${SES_FROM:-}"
DRYRUN_INBOX="${DRYRUN_INBOX:-}"
NOVA_MODEL_ID="${NOVA_MODEL_ID:-amazon.nova-lite-v1:0}"

# Deployment must be explicitly approved before this script is run.
fail() { echo "Deployment preflight failed: $*" >&2; exit 1; }
[[ "$PROFILE" == hackathon ]] || fail "AWS_PROFILE must be hackathon"
[[ "$REGION" == ap-southeast-2 ]] || fail "AWS_REGION must be ap-southeast-2"
[[ "$STACK_NAME" == argus ]] || fail "STACK_NAME must be argus"
[[ "$NOVA_MODEL_ID" == amazon.nova-lite-v1:0 ]] || fail "Only the regional Nova Lite model is permitted"
[[ "${EXPECTED_AWS_ACCOUNT_ID:-}" =~ ^[0-9]{12}$ ]] || fail "Set EXPECTED_AWS_ACCOUNT_ID to the verified hackathon project ID"
[[ -n "$SES_FROM" && -n "$DRYRUN_INBOX" ]] || fail "Set SES_FROM and DRYRUN_INBOX to verified email identities"
[[ "$SES_FROM" != *@example.com && "$DRYRUN_INBOX" != *@example.com ]] || fail "Example email addresses cannot be used for deployment"
for tool in aws sam; do command -v "$tool" >/dev/null || fail "$tool is required"; done

ACTUAL_ACCOUNT_ID=$(aws sts get-caller-identity --profile "$PROFILE" --region "$REGION" --query Account --output text)
[[ "$ACTUAL_ACCOUNT_ID" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || fail "hackathon project does not match EXPECTED_AWS_ACCOUNT_ID"
for identity in "$SES_FROM" "$DRYRUN_INBOX"; do
  VERIFIED=$(aws sesv2 get-email-identity --profile "$PROFILE" --region "$REGION" --email-identity "$identity" --query VerifiedForSendingStatus --output text)
  [[ "$VERIFIED" == True ]] || fail "SES email identity must be verified: $identity"
done
MODEL_TYPES=$(aws bedrock get-foundation-model --profile "$PROFILE" --region "$REGION" --model-identifier "$NOVA_MODEL_ID" --query 'modelDetails.inferenceTypesSupported' --output text)
[[ "$MODEL_TYPES" == *ON_DEMAND* ]] || fail "Regional on-demand inference is unavailable"
# Availability does not prove invocation permissions; do not invoke during preflight.
sam validate --lint --region "$REGION" --profile "$PROFILE"

echo "=================================================="
echo "  Deploying Argus via AWS SAM"
echo "  Region:      $REGION"
echo "  Profile:     $PROFILE"
echo "  Stack Name:  $STACK_NAME"
echo "=================================================="

# 1. Build SAM artifacts
echo "[*] Building SAM application..."
sam build --profile "$PROFILE" --region "$REGION"

# 2. Deploy SAM template using samconfig.toml parameters
echo "[*] Deploying SAM stack..."
sam deploy \
  --stack-name "$STACK_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-fail-on-empty-changeset \
  --parameter-overrides \
    FrontendOrigin="$FRONTEND_ORIGIN" \
    SesFrom="$SES_FROM" \
    DryRunInbox="$DRYRUN_INBOX" \
    NovaModelId="$NOVA_MODEL_ID"

echo ""
echo "[+] Deployment complete! Stack Outputs:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query "Stacks[0].Outputs" \
  --output table

API_BASE=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiBase'].OutputValue" \
  --output text)

echo ""
echo "=================================================="
echo "  NEXT STEPS (Execute in order from docs/HUMAN_TODO.md):"
echo "=================================================="
echo "1. Seed DynamoDB demo cases and assets:"
echo "   python scripts/seed_demo.py --profile $PROFILE --region $REGION"
echo ""
echo "2. Build production frontend:"
echo "   cd frontend"
echo "   VITE_API_BASE=\"$API_BASE\" VITE_AWS_REGION=ap-southeast-2 VITE_LOCATION_API_KEY=\"<your-api-key>\" npm run build"
echo "   (cd dist && zip -r ../dist.zip .)"
echo ""
echo "3. Run Smoke Test against API:"
echo "   ./scripts/smoke_test.sh \"$API_BASE\""
echo "=================================================="
