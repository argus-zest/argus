#!/usr/bin/env bash
set -euo pipefail

PROFILE="${AWS_PROFILE:-hackathon}"
REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-argus}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-http://localhost:5173}"
SES_FROM="${SES_FROM:-noreply@example.com}"
DRYRUN_INBOX="${DRYRUN_INBOX:-dryrun@example.com}"
NOVA_MODEL_ID="${NOVA_MODEL_ID:-global.amazon.nova-2-lite-v1:0}"

echo "=================================================="
echo "  Deploying Argus via AWS SAM"
echo "  Region:      $REGION"
echo "  Profile:     $PROFILE"
echo "  Stack Name:  $STACK_NAME"
echo "=================================================="

# 1. Build SAM artifacts
echo "[*] Building SAM application..."
sam build

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
echo "   VITE_API_BASE=\"$API_BASE\" VITE_LOCATION_API_KEY=\"<your-api-key>\" npm run build"
echo "   (cd dist && zip -r ../dist.zip .)"
echo ""
echo "3. Run Smoke Test against API:"
echo "   ./scripts/smoke_test.sh \"$API_BASE\""
echo "=================================================="
