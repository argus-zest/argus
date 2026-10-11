# Proposed Argus deployment — 2026-10-11

> Historical checkpoint: superseded by [AWS_EXECUTION_HANDOFF.md](AWS_EXECUTION_HANDOFF.md) for current security findings, validation results, and deployment instructions.

Status: prepared locally; deployment is not approved. No stack, change set, resources, or test emails were created.

## Target and parameters

- AWS project: `262952461520`; role `AccountFullAccessRole`. User-verified hackathon identity matches refreshed MCP STS. The hackathon CLI independently confirmed the same project and role at the connectivity checkpoint.
- CLI profile `hackathon`, Region `ap-southeast-2`, stack `argus`.
- API and S3 CORS allow exactly `http://localhost:5173` and `https://demo.d1ygq6l84twsei.amplifyapp.com`.
- `SesFrom=chauhanansh1046@gmail.com`, `DryRunInbox=chauhanansh1046@gmail.com`: both selected by the user, identity verified through SES in Sydney. SES remains in sandbox. Preserve dry-run routing; no external recipient tests are authorized.
- `NovaModelId=amazon.nova-lite-v1:0`: active, on-demand regional model with text/image/video input and text output. Invoke permission and application runtime acceptance remain untested. No global inference profile or cross-Region fallback.
- Optional `EnableTomtom=false`, `TomtomApiKey` empty. Production `USE_MOCKS=false`.
- Expected application bucket `argus-262952461520-ap-southeast-2`; this is a proposed name, not an actual deployed output.

## Gates before deployment

1. Completed: package networking works; SAM 1.168.0 installed in .venv-sam; lockfile repaired and npm ci passed.
2. Completed: SAM lint/build, frontend strict TypeScript, 17 Vitest tests, and production build passed. CloudFormation ValidateTemplate passed, but only checks template syntax. Native frontend checks passed 12 tests; contract-boundary checks passed 2 tests. The refreshed complete backend suite passed 62 tests in 52.25 seconds, preserving all previous 45 tests.
3. Completed: STS, SES, empty queried inventory, and regional model availability independently refreshed with hackathon. Do not change global credentials or MCP configuration.
4. Pending: dependency advisory remediation/review (14 advisories, three critical), policy refinement, final template review, charges, and creation/replacement risks. Request explicit deployment approval before invoking the deployment script or creating a change set.

Only after these gates and explicit approval, use the existing deployment script:

```bash
PATH="$PWD/.venv-sam/bin:$PATH" \
__SAM_CLI_APP_DIR="$PWD/.cache/sam-config" SAM_CLI_TELEMETRY=0 \
AWS_PROFILE=hackathon AWS_REGION=ap-southeast-2 \
EXPECTED_AWS_ACCOUNT_ID=262952461520 \
SES_FROM=chauhanansh1046@gmail.com \
DRYRUN_INBOX=chauhanansh1046@gmail.com \
FRONTEND_ORIGIN=http://localhost:5173 \
NOVA_MODEL_ID=amazon.nova-lite-v1:0 bash scripts/deploy.sh
```

The script validates identity and verified email identities, runs SAM lint/build, and deploys stack argus with CAPABILITY_IAM and --resolve-s3. SAM configuration requires change-set confirmation. Do not bypass failed SAM operations with manually duplicated resources.

## Infrastructure and costs

The queried Sydney inventory returned no CloudFormation stacks, Lambda functions, DynamoDB tables, HTTP APIs, state machines, EventBridge rules, or S3 buckets. The plan creates the resources defined by the existing SAM template: HTTP API, application functions and layer, three DynamoDB tables, private evidence bucket, escalation workflow, and scheduled scoring integration. SAM artifact packaging can also create an artifact bucket. Actual changes require change-set review; inventory alone does not prove absence of conflicts.

Bucket protections include all public-access blocks, AES256 encryption, versioning, GET/PUT/HEAD CORS, and retention on deletion/replacement. Tables are retained too. No blanket uploads expiration is configured because case evidence still depends on these keys. An S3 policy now denies insecure application access to both bucket and objects, exempting direct AWS service principals whose transport context can be redacted. Tighter SES identity/prefix-level application permissions remain review follow-ups; Autopilot analysis is now available and completed, but emitted broad permissions that have not been accepted or applied.

Potential charges include packaging/storage/versions, API Gateway, Lambda, DynamoDB, hourly scoring, Step Functions, logs, SES, and Bedrock inference. Free Tier reports FREE/ACTIVE with USD 120 credits remaining at inspection; this is not a zero-cost guarantee. No billable inference or deployment test has been approved.

## After an approved deployment

Read actual outputs using `aws cloudformation describe-stacks --profile hackathon --region ap-southeast-2 --stack-name argus`. Capture ApiBase, BucketName, StateMachineArn, TableNames, AssetsTableName, CasesTableName, and CaseEventsTableName where returned. Populate INTEGRATION_HANDOFF.md with actual outputs, not guessed identifiers.

Health/read tests, browser CORS checks, uploads, persistence, inference, escalation, and email delivery are not yet verified. Obtain bounded approval for writes, billable inference, and email tests. Argus Mobile remains outside this session's repository access and testing scope.

## IAM analysis review

The AWS IAM skill requires source-derived identity policies to use deterministic Autopilot analysis. The tool is now installed in the repository-local uv cache, and the following local analysis completed for the notice function and shared Bedrock client. No replacement identity policy was applied:

```bash
UV_CACHE_DIR="$PWD/.cache/uv" uvx iam-policy-autopilot@latest generate-policies \
  "$PWD/backend/functions/sfn_notice_agent/app.py" \
  "$PWD/backend/layer/python/common/nova.py" \
  --region ap-southeast-2 --account 262952461520 \
  --service-hints ses s3 dynamodb bedrock-runtime --pretty
```

Flags were confirmed with --help. Output remains in ignored .cache/notice-iam-analysis.json. It includes unresolved resource wildcards and broad dependency/replication actions; it is a review baseline, not an approved least-privilege policy. Do not use --upload-policies. Review runtime resource resolution and dry-run recipient restrictions before incorporating any generated policy into SAM. AWS documents [SES sender and recipient conditions](https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html) and the [S3 service-principal transport exception](https://docs.aws.amazon.com/AmazonS3/latest/userguide/amazon-s3-policy-keys.html).
