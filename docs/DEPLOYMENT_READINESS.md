# Deployment readiness — 2026-10-11

> Historical checkpoint: superseded by [AWS_EXECUTION_HANDOFF.md](AWS_EXECUTION_HANDOFF.md) for current security findings, validation results, and deployment instructions.

No deployment, infrastructure mutation, email delivery, or billable inference was performed. SPEC.md remains unchanged. Frontend repairs were committed separately on dev/web-latest; the user subsequently confirmed publishing that branch. GitHub remains unreachable from this shell, so publication was not independently reverified. AWS preparation remains uncommitted on feat/aws-integration and requires review before deployment.

## Identity and read-only findings

| Check | Result |
|---|---|
| CLI `hackathon` STS | Verified project 262952461520, assumed AccountFullAccessRole |
| User-verified `hackathon` identity | Project `262952461520`, `AccountFullAccessRole`, Sydney |
| MCP STS | Independently confirmed project `262952461520`, assumed `AccountFullAccessRole` |
| MCP/profile compatibility | Both independently verified identities match project 262952461520 |
| Free Tier | FREE, ACTIVE; USD 120 remaining credits reported, expiration 2027-04-10 |
| SES | Sandbox, sending enabled; selected sender and dry-run inbox both verified |

Read-only findings were independently refreshed using the hackathon CLI profile in Sydney after checking STS identity:

- No CloudFormation stacks, Lambda functions, DynamoDB tables, HTTP APIs, Step Functions state machines, EventBridge rules, or S3 buckets returned. This inventory covers the queried services, not every AWS service.
- SES: `ProductionAccessEnabled=false`, `SendingEnabled=true`, enforcement HEALTHY. `chauhanansh1046@gmail.com` is verified for sending. The user selected it for both SesFrom and DryRunInbox; sandbox sender/recipient identity requirements are satisfied for that configuration. Quota 200/day and 1/second. No email was sent by this session.
- Nova Lite: ACTIVE; TEXT/IMAGE/VIDEO input, TEXT output, ON_DEMAND supported. Catalog availability does not prove runtime invoke permission.
- CloudFormation's read-only ValidateTemplate accepted the actual local SAM template and its six parameters. It reported CAPABILITY_AUTO_EXPAND for the raw SAM transform. This syntax check does not replace SAM lint/build, change-set review, or runtime validation.

No global credentials or MCP/OpenCode configuration was changed. No MCP profile change is required merely to match project identity. All eventual deployment operations must explicitly use the hackathon CLI profile, verify the expected project ID, and obtain deployment approval. Credits do not guarantee zero costs.

## Regional model and request compatibility

Keep `amazon.nova-lite-v1:0` at the Sydney Bedrock Runtime endpoint. IAM permits `bedrock:InvokeModel` on `arn:aws:bedrock:ap-southeast-2::foundation-model/amazon.nova-lite-v1:0`; this is the foundation-model ARN, with no project ID. No inference-profile ARN or Region wildcard is needed for direct regional invocation.

[AWS Nova Lite model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-lite.html) documents Sydney In-Region inference, images/text/video, Converse, and client-side tool use. [Global inference documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/global-cross-region-inference.html) describes routing beyond a single Region and cannot satisfy this project's policy.

The existing application uses Converse messages, image byte blocks, explicit bounded `maxTokens`, and tool schemas for hazard analysis and repair verification, plus text prompts for clauses and notices. Tool JSON schemas are not the separate structured-output feature (which Nova Lite does not support). Actual model permissions, response quality, and runtime request acceptance remain untested in the intended project. No billable inference was performed. No cross-Region fallback is permitted.

The restored frontend `src/lib/` client implements read-only fixtures only when `VITE_USE_MOCKS=true` AND Vite development mode is active. The UI displays a mock-data banner. Live weather, uploads, analysis, and case operations cannot silently use these fixtures. Production rejects mock configuration and connection failures never trigger a fallback.

Backend inference fixtures require `USE_MOCKS=true` AND `ARGUS_ENV=local`; deployed Lambda execution is rejected unless explicitly running under SAM Local. Analysis returns unclear/zero confidence, repair verification never approves closure, and clause extraction never claims a quote was found. Responses carry `mock=true` and `source=local_mock`. Untyped Converse/notice drafting does not fabricate model output; the notice agent's deterministic template fallback remains identifiable. These fixtures do not mock S3, DynamoDB, Step Functions, or SES: use separate local test doubles for those dependencies. Production SAM still sets USE_MOCKS=false. RDD2022 evaluation refuses mock inference so fixtures cannot become reported model metrics.

## Local infrastructure changes and risks

- Existing SAM resources and deployment script retained. No duplicate manual resources.
- Removed example SES defaults from SAM parameters/config; sender/inbox must be supplied and verified.
- Deployment preflight refuses wrong profile, Region, stack, model, project identity, and unverified sender/inbox. Require `EXPECTED_AWS_ACCOUNT_ID` after STS verification. Model catalog check is read-only and does not invoke.
- S3 bucket remains `argus-${AWS::AccountId}-ap-southeast-2`; all four public-access blocks retained, explicit AES256 encryption and versioning added. Existing GET/PUT/HEAD CORS retained for FrontendOrigin and localhost:5173.
- Removed blanket 14-day uploads expiration: case photo keys remain under uploads/ and are used by case views, repair verification, and notices. There is no promotion/tagging mechanism proving these objects are temporary. Add expiration only after a reviewed evidence-retention design.
- Bucket and three DynamoDB tables now retain on stack deletion/replacement. Retained resources and S3 versions continue accruing storage costs and need deliberate lifecycle management.
- Added separate table-name outputs while preserving existing TableNames, ApiBase, BucketName, and StateMachineArn outputs.
- Existing IAM access is scoped to application tables/bucket and the regional model; SES remains scoped to regional identity/*, and task-token callback permissions use '*'. A stricter sender/recipient policy and prefix-level S3 review remain follow-up work. A local bucket policy now denies insecure application transport on the bucket and all objects, excluding direct AWS service principals as AWS recommends. Read-only CloudFormation syntax validation passed after this addition. Autopilot analysis now completed locally. Its output includes wildcard Bedrock resources, replication permissions, and other broad actions; it has NOT been incorporated into SAM. Sender/recipient and prefix-level policy refinement remains pending review.

No local edit requests replacement of an existing named bucket/table. Region migration could require new resources if an old stack exists elsewhere; no cross-Region migration is authorized. Inventory was empty for the queried services; a reviewed CloudFormation change set is still required to establish actual replacement/destruction risks. A fixed bucket name conflicts if an unmanaged bucket with that name already exists; do not create a duplicate or bypass SAM.

Potential charges: API Gateway, Lambda, DynamoDB reads/writes/storage, S3 objects/versions/artifact bucket/requests, Bedrock tokens, SES, Step Functions transitions, and CloudWatch logs. Hourly scheduled scoring is enabled. No cost estimate or Free Tier guarantee is asserted. Check AWS Settings > Billing and project spend limits before approval; confirm selected Region at AWS Settings > View all projects > Overview > Additional Info > Region.

## Validation and deployment checkpoint

- Repository-local SAM CLI 1.168.0: `sam validate --lint --region ap-southeast-2 --profile hackathon` passed.
- `sam build --region ap-southeast-2 --profile hackathon` passed; artifacts in ignored .aws-sam/build. Function dependencies use the Lambda-provided boto3/botocore and standard library; shared-layer source has no external package requirements.
- Frontend src/lib API/type modules restored, with generated contract validators and a frontend-specific gitignore exception. Restored client accepts actual local read-handler responses.
- `npm run build --prefix frontend`: passed (TypeScript and Vite production build). Main JS bundle 1,085.32 kB, gzip 297.81 kB; Vite warns about chunk size.
- `npm test --prefix frontend`: 17 tests passed, including all six restored-client tests.
- `frontend/node_modules/.bin/tsc --noEmit`: passed with strict configuration.
- Local YAML/TOML parsing, Region/model/bucket/public-access/retention consistency checks, shell syntax, and Git whitespace checks passed.
- Backend suite and added tests: see LOCAL_VALIDATION.md for the latest complete run; all original 45 tests retained.
- `npm run test:api --prefix frontend`: 12 dependency-free API runtime checks passed using Node 24, including requests, response validation, errors, uploads, and mock isolation.
- Playwright Chromium: desktop mock banner, fallback map rendering, report/cases/evidence/architecture panels passed with no page errors. Narrow 390px layout clips controls and compresses panels; no live backend workflow was tested.
- Live API, CORS, S3 upload, case persistence, escalation, SES delivery, and inference tests have not been run.
- Network now works for GitHub, npm, PyPI, and Sydney AWS endpoints. SAM installed in .venv-sam; no global installation or credential changes.
- npm ci initially detected incomplete lock entries. npm install --package-lock-only repaired missing transitive type packages/hoisting; declared dependency versions and previously locked package versions were retained. Subsequent npm ci passed.
- npm audit reports 14 advisories (5 moderate, 6 high, 3 critical), including MapLibre, Vitest and tinypool. No forced or major dependency upgrades were made. Review remediation before production deployment.

Local lint, build, frontend type checks and tests are now complete. SES sender/inbox and target identity are verified. Dependency security remediation and actual change-set/cost review remain required before production readiness. Deployment itself still requires explicit approval. See VALIDATION_2026-10-11.md for the current checkpoint.

Only AFTER explicit deployment approval, use existing script with actual verified values:

```bash
AWS_PROFILE=hackathon AWS_REGION=ap-southeast-2 \
EXPECTED_AWS_ACCOUNT_ID=262952461520 \
SES_FROM=chauhanansh1046@gmail.com DRYRUN_INBOX=chauhanansh1046@gmail.com \
FRONTEND_ORIGIN=http://localhost:5173 \
NOVA_MODEL_ID=amazon.nova-lite-v1:0 bash scripts/deploy.sh
```

Script uses stack argus, CAPABILITY_IAM, resolve-s3, and actual template parameters FrontendOrigin, SesFrom, DryRunInbox, NovaModelId. Optional EnableTomtom/TomtomApiKey remain disabled/empty by default. Do not run seed/reset/smoke workflows until their writes/inference/email scope has separate bounded approval.

After approved deployment, describe stack outputs with hackathon in Sydney and populate the integration handoff with actual values. No deployment approval has been requested or granted. Local build gates now pass; dependency advisories and permission refinement remain documented review items. See DEPLOYMENT_PLAN.md for the concrete proposed configuration.
