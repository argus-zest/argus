# Argus Web AWS execution plan — 2026-10-11

This is the authoritative current execution reference. Older checkpoint documents describe historical results. **User approved the Sydney SAM deployment and bounded live tests (disposable seeds, one uploaded report/case, up to 10 regional model calls and five dry-run emails to the verified inbox). The application stack has deployed successfully; live upload, manual report persistence and browser retrieval passed. The targeted timeout-context workflow update reached UPDATE_COMPLETE; successful four-rung escalation and AI inference are not claimed.** The immediate objective is an honest, bounded hackathon demo, not production certification.

## Working tree and preservation

- Working directory: `/home/ansh/Projects/argus-aws/argus`.
- Branch: `feat/aws-integration`; HEAD `3ff38ebf0e5168b2e7ab7a73b19df061bdcacb4f`.
- Origin: `https://github.com/argus-zest/argus`; do not change remotes or push automatically.
- The current implementation includes substantial **uncommitted** AWS integration, frontend dependency/layout fixes, infrastructure policies, tests, and documentation. Preserve it. Do not reset, clean, stash, switch branches, recreate commits, or merge the teammate's animation branch.
- `dev/web-latest` is the separately published teammate baseline. `feat/animation-update` remains independent. Argus Mobile is outside this task; never access it.
- `SPEC.md` remains unchanged. Runtime and infrastructure follow the assigned Region instead of the original specification.
- `.cache/`, `.aws-sam/`, `.venv-sam/`, `.tools/`, node_modules, dist, and local environment files are ignored. Targeted secret scanning found no AWS access-key IDs, GitHub tokens, or private-key headers in publishable files. No tracked local `.env` files were found. This is a targeted check, not a guarantee about all historical commits.

## Verified target and service prerequisites

| Setting | Verified value / limitation |
|---|---|
| AWS project ID | `262952461520` |
| CLI profile / role | `hackathon` / `AccountFullAccessRole`; CLI STS and MCP STS independently match |
| Selected Region | `ap-southeast-2` only |
| Stack | `argus` |
| SES sender and dry-run inbox | `chauhanansh1046@gmail.com` for both; explicitly selected by user and verified in Sydney |
| SES status | HEALTHY, sending enabled, sandbox; production access disabled; 200 messages/day, 1/second at inspection |
| Bedrock | `amazon.nova-lite-v1:0`, ACTIVE, ON_DEMAND; TEXT/IMAGE/VIDEO input, TEXT output |
| Model ARN | `arn:aws:bedrock:ap-southeast-2::foundation-model/amazon.nova-lite-v1:0` |
| Free Tier | FREE/ACTIVE, USD 120 credits at inspection, expiry 2027-04-10; not a zero-cost guarantee |
| Existing infrastructure | Queried stacks, S3 buckets, Lambdas, DynamoDB tables, HTTP APIs, state machines and EventBridge rules returned empty; not an exhaustive inventory |
| Actual deployed outputs | None yet. Do not invent an API ID, URL, ARN or deployment result. |

The direct regional model uses Converse, authorized by `bedrock:InvokeModel` on the exact model ARN. No inference profile, global Nova 2 Lite, cross-Region fallback, or wildcard foundation-model permission is configured. Model listing and IAM simulation do not prove successful invocation or multimodal output quality. No billable invocation has been performed.

CLI login briefly expired and attempted to refresh a read-only home cache. The user refreshed `aws login --profile hackathon` in their normal terminal; a subsequent CLI STS check passed. If this recurs, ask for the same interactive refresh. Never change global AWS/MCP configuration or copy credentials into source/environment templates.

## Essential validation checkpoint

- Backend: **82 tests passed, including actual imports of all 14 SAM handlers and real SDK Sydney Signature V4 presigning**, retaining the previous 45/62-test coverage.
- SAM CLI **1.168.0**, Python 3.12, installed locally in `.venv-sam`; lint and build passed.
- Strict TypeScript passed; **17 Vitest tests** and **12 API runtime checks** passed; production Vite build passed.
- Browser Chromium: 1440×900, 390×844, 768×1024 and 1024×768 passed navigation, map fallback rendering, four modal openings, scenario changes and keyboard reset; no page errors. The actual MapLibre attribution-control malicious-attribute fixture was sanitized without execution.
- Narrow layout fixed by stacking panels below the desktop breakpoint, wrapping navigation, reserving map height, and stacking the cases list/detail view on small screens. Animation logic was untouched.
- Browser tests use **explicitly labeled, read-only local fixtures** and OpenStreetMap fallback. They do not establish live AWS Location, upload/persistence, Bedrock, SES, physical-device or PWA functionality.
- Production bundle: 1,228.30 kB JS / 328.62 kB gzip; chunk-size warning is non-blocking for the demo.
- Region scan found no inappropriate original-Region or global-model references in deployment/runtime files. Git whitespace check passed; SPEC diff is empty.
- SAM warns that function requirements files are absent: functions use standard library and Lambda-provided boto3/botocore. This does not prove the deployed SDK version supports every feature; inspect runtime errors after approval.

Local repeat commands, from the repository root:

```bash
pytest -q
__SAM_CLI_APP_DIR="$PWD/.cache/sam-config" SAM_CLI_TELEMETRY=0 \
  .venv-sam/bin/sam validate --lint --region ap-southeast-2
__SAM_CLI_APP_DIR="$PWD/.cache/sam-config" SAM_CLI_TELEMETRY=0 \
  .venv-sam/bin/sam build --region ap-southeast-2
(cd frontend && npm ci && npx tsc --noEmit && npm test && npm run test:api && npm run build)
git diff --check
```

The SAM metadata-directory override avoids writing the sandbox's read-only home; it is an internal setting verified in the installed version. Node 20+ is required; tests ran under Node 24.21.0/npm 12.2.0. Do not approve unrelated npm lifecycle scripts globally.

For reproducible browser checks, run `VITE_USE_MOCKS=true npm run dev -- --host 127.0.0.1 --port 5173 --strictPort` from frontend in one terminal, then `python frontend/scripts/browser_smoke.py` from the root with Playwright Chromium available. Screenshots/results go to ignored `.cache/security-layout/`. Stop the mock server before the live demo; never describe these fixtures as live backend behavior.

## Dependency security disposition

Initial `npm audit`: 14 entries, including three critical. Updated lockfile: **zero production advisories**, **zero critical advisories**, five high development-only entries. Audit counts include transitive affected packages, not 14 independent flaws.

| Original entry | Scope | Resolution / disposition |
|---|---|---|
| maplibre-gl, critical | Production | 4.7.1 → **6.4.1**, first patched release for attribution sanitizer bypass; required major migration validated with namespace import, build and actual browser sanitizer fixture |
| vitest, critical | Development | 1.6.1 → **4.1.11**; fixes UI/server issues and newly discovered mocker advisory; all tests pass |
| tinypool, critical | Development | Vulnerable 0/1.x chain removed by Vitest 4 |
| vite, high | Development | 5.4.21 → **6.4.3**, patched supported major; React plugin remains compatible |
| esbuild, moderate | Development | Updated transitively to patched 0.25.12 |
| @vitejs/plugin-react, moderate | Development | Vite dependency fixed; no unnecessary plugin-major change |
| vite-node, moderate | Development | Old Vitest/Vite chain removed |
| postcss-selector-parser, moderate | Development | Exact **7.1.6** override, first patched release; existing Tailwind 3 build validated |
| postcss-nested, moderate | Development | Fixed parser dependency |
| braces, high | Development | **Unresolved** nested-pattern stack-exhaustion DoS; latest published 3.0.3 remains affected; no patched release at inspection |
| chokidar, high | Development | Affected via braces; unresolved |
| micromatch, high | Development | Affected via braces; unresolved |
| fast-glob, high | Development | Affected via micromatch/braces; unresolved |
| tailwindcss, high | Development | Remaining aggregate finding via glob tooling; parser finding resolved |

The remaining chain processes fixed, repository-owned Tailwind content globs; it is absent from the production dependency audit. Untrusted build configuration can still cause build/watch denial of service. Keep build inputs trusted, do not expose Vite/Vitest development servers publicly, and do not claim the full audit is clean. No `npm audit fix --force` was used; no Tailwind redesign was introduced.

```bash
(cd frontend
 npm audit
 npm audit --omit=dev
)
```

Run these separately: the full audit currently exits nonzero, so shell `&&` would skip the production audit. Upstream references: [MapLibre](https://github.com/maplibre/maplibre-gl-js/security/advisories/GHSA-jrc7-96c5-q579), [Vitest](https://github.com/advisories/GHSA-5xrq-8626-4rwp), [mocker](https://github.com/advisories/GHSA-82fw-gwwq-j7x9), [braces](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm).

## IAM and infrastructure security

Source-derived IAM analysis ran using IAM Policy Autopilot 0.3.0 against runtime files. Broad optional replication, KMS, tagging, guardrail and bearer-tool actions from the analyzer were deliberately excluded because this application does not use them. All 14 Lambda roles and the workflow role are explicit CloudFormation resources, with separate scoped logs permissions and these runtime grants:

| Role/function | Application permissions |
|---|---|
| Health, Hotspots | Logs only |
| Risk | Read exact `exports/latest_scores.json` |
| Assets | Scan Assets table |
| EvalResults | Read `eval/*` |
| ScheduledScore | Put exact `exports/latest_scores.json` |
| Presign | Put `uploads/*` |
| Analyze | Read `uploads/*`; invoke exact regional Nova Lite |
| TenderClause | Read `tenders/*`; invoke exact regional Nova Lite |
| Cases | Get/put/update/scan Cases; put/query CaseEvents; read `uploads/*` for evidence links; start the single workflow |
| ClaimFix | Get/update Cases; put CaseEvents; read `uploads/*`; regional Nova Lite; task success/failure callbacks |
| RegisterToken | Update Cases |
| MarkClosed | Update Cases; put CaseEvents |
| NoticeAgent | Get Cases; query/put CaseEvents; read `uploads/*`; regional Nova Lite; restricted SES SendEmail |
| Workflow | Invoke only NoticeAgent, RegisterToken and MarkClosed |

SES permissions require the exact configured sender identity, `ses:FromAddress` equality, and **all** recipients equal the configured dry-run inbox; `Null=false` prevents vacuous recipient-condition success. No SendRawEmail permission. Step Functions task-token APIs require `Resource="*"`; this documented exception is constrained by `aws:RequestedRegion=ap-southeast-2`. Workflow trust restricts SourceAccount and the SAM-generated state-machine logical-name prefix in the verified project and Region. Lambda execution trust uses the service principal, without unsupported invented SourceArn conditions.

AWS Access Analyzer validated all **15** final identity policies with **no findings**. Of 16 policy simulations, 15 matched allow/deny expectations, including external/missing SES recipients, wrong sender, wrong S3 prefix, wrong model, wrong table and wrong workflow target. Own-log-stream permission returned implicitDeny even for exact-ARN and unrestricted control policies. This is an unresolved simulator limitation/diagnostic, not evidence that broadening the production role would fix it. Policy scope follows the [CloudWatch Logs resource documentation](https://docs.aws.amazon.com/service-authorization/latest/reference/list_logs.html). Verify actual Lambda logging immediately after approved deployment; no logging success is claimed.

`scripts/validate_iam.py --materialize-only` writes proposed parameter-resolved policies to ignored `.cache/iam-review/` without AWS calls. `python scripts/validate_iam.py` performs read-only Access Analyzer validation; `python scripts/simulate_iam.py` runs the full read-only simulation matrix and currently exits nonzero on the logging diagnostic. Synthetic `CHECK` ARNs are simulation inputs, not deployed identifiers. These checks do not simulate project SCPs/RCPs or prove actual runtime access.

**cfn-guard 3.2.1** was installed in ignored `.tools/cfn-guard` after user approval. AWS registry rules are pinned at commit `7f7340c26ae5d5e8874651dbffeb12e0e9f505b6` under `infra/security/aws`. Four applicable S3 checks pass (public read/write prohibited, encryption, versioning); two standalone-IAM-policy checks skip because policies are inline roles. The upstream TLS rule reports a **reviewed representation mismatch**: it checks boolean `false`, while valid IAM conditions use string `'false'`. The project's `infra/security/argus.guard` validates that exact TLS deny, production mock prohibition, the regional model allowlist and absence of wildcard runtime actions; all three project rules pass. Python infrastructure tests additionally verify exact bucket/object deny resources, retained evidence and role scopes. The full upstream registry command therefore still exits nonzero; do not hide or call that result an unrestricted compliance pass.

```bash
.tools/cfn-guard/cfn-guard validate --rules infra/security/aws --data template.yaml \
  --output-format json --structured --show-summary none
.tools/cfn-guard/cfn-guard validate --rules infra/security/argus.guard --data template.yaml \
  --output-format json --structured --show-summary none
```

Evidence bucket: all four public-access blocks, AES256, versioning, HTTPS-only application access, GET/PUT/HEAD CORS for localhost and FrontendOrigin. Bucket and three tables have DeletionPolicy/UpdateReplacePolicy Retain. **No blanket 14-day uploads expiration:** case evidence still references these objects. Logs currently have no retention limit and may accumulate charges. API throttles are 20 requests/second, burst 40, but **there is no authentication**. CORS is not authentication. Use only disposable demo data, restrict demonstration duration, and require authentication/abuse controls before production or private-user-data use.

## Exact resources and dependency order

SAM declares one HTTP API/default stage, one shared Python layer, one evidence S3 bucket and its deny policy, three PAY_PER_REQUEST DynamoDB tables (`argus-Assets`, `argus-Cases`, `argus-CaseEvents`), 14 Lambda functions, 15 execution roles, one Standard escalation state machine, and one hourly EventBridge schedule. SAM generates API integrations, routes and invoke permissions. Function logical IDs: HealthFunction, HotspotsFunction, RiskFunction, AssetsFunction, EvalResultsFunction, ScheduledScoreFunction, PresignFunction, AnalyzeFunction, TenderClauseFunction, CasesFunction, ClaimFixFunction, RegisterTokenFunction, MarkClosedFunction, NoticeAgentFunction.

`--resolve-s3` can create a separate SAM-managed artifact bucket/stack. Lambda-created log groups are additional runtime resources. No Cognito, frontend hosting, AWS Location map/key, WAF or cross-Region resources are included. No duplicate manual provisioning is permitted.

Order: refreshed identity/SES/model checks → local lint/build → **approval** → SAM packaging/change-set creation and review → stack deployment → actual outputs → authorized seed/write tests → frontend live configuration → read tests/CORS → bounded upload/report/persistence/retrieval → optional approved inference/SES/workflow tests → demo recording.

This is an initial stack based on the empty queried inventory. Expected changes are additions, not data deletion. On a subsequent deployment, role policies update in place; changes to bucket/table names or other immutable properties may require replacement and must be reviewed. Retain protects data but creates orphan/name conflicts after rollback/deletion; never resolve those by deleting evidence.

## Approval and exact deployment command

**Approval A — provisioning:** user must approve creation of the stack, artifact packaging resources, scoped IAM roles, hourly schedule, potential charges and temporary unauthenticated demo API. Review AWS Settings > Billing for credits/spend limit and AWS Settings > View all projects > Overview > Additional Info > Region. Approval was received in-session; creation is in progress.

**Approval B — bounded live demo tests:** request authorization for disposable S3 objects, DynamoDB test records, one report/workflow, resulting dry-run email to the verified inbox and a small regional Bedrock invocation budget. Creating a case starts its escalation workflow and may send repeated dry-run messages. Do not treat report creation as a harmless read.

Only after Approval A, run from root:

```bash
AWS_LOGIN_CACHE_DIRECTORY="$PWD/.cache/aws-login" \
PATH="$PWD/.venv-sam/bin:$PATH" \
__SAM_CLI_APP_DIR="$PWD/.cache/sam-config" SAM_CLI_TELEMETRY=0 \
AWS_PROFILE=hackathon AWS_REGION=ap-southeast-2 \
EXPECTED_AWS_ACCOUNT_ID=262952461520 \
SES_FROM=chauhanansh1046@gmail.com DRYRUN_INBOX=chauhanansh1046@gmail.com \
FRONTEND_ORIGIN=http://localhost:5173 NOVA_MODEL_ID=amazon.nova-lite-v1:0 \
bash scripts/deploy.sh
```

The script checks identity, SES identity verification and regional ON_DEMAND model availability, runs lint/build, then executes:

```bash
sam deploy --stack-name argus --profile hackathon --region ap-southeast-2 \
  --capabilities CAPABILITY_IAM --resolve-s3 --no-fail-on-empty-changeset \
  --parameter-overrides FrontendOrigin=http://localhost:5173 \
    SesFrom=chauhanansh1046@gmail.com DryRunInbox=chauhanansh1046@gmail.com \
    NovaModelId=amazon.nova-lite-v1:0
```

`samconfig.toml` enables change-set confirmation; do not disable it, disable rollback, or force replacements. EnableTomtom remains false and TomtomApiKey empty. USE_MOCKS is hardcoded false in deployment. `sam deploy --no-execute-changeset` is **also approval-gated**, because packaging and change-set creation can mutate infrastructure. Do not use MCP to bypass a failed SAM operation.

## Outputs and frontend connectivity

After successful approved deployment:

```bash
aws cloudformation describe-stacks --profile hackathon --region ap-southeast-2 \
  --stack-name argus --query 'Stacks[0].{Status:StackStatus,Outputs:Outputs}' --output json
API_BASE=$(aws cloudformation describe-stacks --profile hackathon --region ap-southeast-2 \
  --stack-name argus --query "Stacks[0].Outputs[?OutputKey=='ApiBase'].OutputValue" --output text)
printf '%s\n' "$API_BASE"
```

Expected keys: ApiBase (includes `/v1`), BucketName (expected `argus-262952461520-ap-southeast-2`), StateMachineArn, TableNames, AssetsTableName, CasesTableName, CaseEventsTableName. Use returned outputs, not guessed ARNs. Write verified values and live/mock results into `docs/INTEGRATION_HANDOFF.md` without credentials.

Start the live frontend at the allowed origin:

```bash
(cd frontend && VITE_API_BASE="$API_BASE" VITE_AWS_REGION=ap-southeast-2 \
  VITE_USE_MOCKS=false npm run dev -- --host 127.0.0.1 --port 5173 --strictPort)
```

Demo URL: `http://localhost:5173`. Use `localhost`, not `127.0.0.1`, in the browser, because CORS allows localhost. Empty/unset VITE_LOCATION_API_KEY selects the existing OpenStreetMap fallback; do not supply an invented or unrestricted Location key. Browser-visible variables are public, not AWS credentials. Production build: `(cd frontend && VITE_API_BASE="$API_BASE" VITE_AWS_REGION=ap-southeast-2 VITE_USE_MOCKS=false npm run build)`. No hosting deployment is included. Vite preview uses another origin by default, so do not switch the live demo to preview without adjusting the approved CORS configuration.

## Smoke tests and honest demo sequence

Read-only after deployment:

```bash
bash scripts/smoke_test.sh "$API_BASE"
curl -fsS "$API_BASE/cases"
curl -i -X OPTIONS "$API_BASE/cases" -H 'Origin: http://localhost:5173' \
  -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: content-type'
```

Smoke script checks health, >=10 hotspots, matching risk count, assets and evaluation response shape. Evaluation endpoint shape does not prove model evaluation was performed. Do not relabel seeded/illustrative results as measurements.

After Approval B, seed existing civic/demo data only if needed: `python scripts/seed_demo.py --profile hackathon --region ap-southeast-2`. Preview with `--dry-run` first. Seeding writes illustrative events; it does not execute inference and can overwrite fixed seed IDs. Never present seeded closure text as an actual tested Nova result.

Bounded live workflow: open Report → select a known hotspot → upload one disposable JPEG/PNG → check the storage PUT succeeded → invoke regional analysis only within the approved budget → submit one report → note its returned case_id → confirm it appears in Cases and persists after page reload → `curl -fsS "$API_BASE/cases/$CASE_ID"` confirms server retrieval. Keep the network panel visible for evidence. The upload contract is POST `/uploads/presign` with `{"purpose":"report","content_type":"image/jpeg"}`, then PUT returned upload_url with matching Content-Type; POST `/analyze` accepts `{"s3_key":"returned-key"}`. Do not log or publish presigned URLs/task tokens.

If Bedrock is denied/unavailable, do not route globally or enable production mocks. Timebox diagnosis using Lambda logs and model prerequisites. Demonstrate read-only fixture mode separately with its explicit banner, or report persistence without claiming AI analysis when the UI/API permits it. The local backend USE_MOCKS mechanism only mocks inference when ARGUS_ENV=local and local-runtime safeguards pass; it does not mock S3, DynamoDB, workflows or email. The frontend fixture mode is read-only and rejects writes. Any live alternative needed to submit a report must be a small, clearly labeled reviewed fix, not fabricated inference.

For the video, explicitly distinguish live API/case persistence, regional AI if actually verified, map fallback, dry-run email and illustrative civic/evaluation data. No physical-device/PWA/live-mobile integration claim.

## Costs and bounded use

Public AWS Sydney price catalogs were inspected; no signed cross-Region application API was used. Rates are USD before taxes, credits and Free Tier: HTTP API $1.29/million requests; Lambda $0.20/million requests and $0.0000166667/GB-second at first tier; S3 $0.025/GB-month, PUT $0.0055/1000, GET $0.00044/1000; DynamoDB $0.71/million write units, $0.1425/million read units and $0.285/GB-month beyond free storage; standard logs $0.67/GB ingestion and $0.033/GB-month; Nova Lite $0.000063/1000 input and $0.000252/1000 output tokens; SES Essentials $0.00016/message at first tier; Standard workflow $0.000025/transition.

Illustrative 30-day gross calculation, performed with Python Decimal: 10,000 HTTP requests, 10,000 Lambda calls (9,280 at 1s/512MB plus 720 hourly runs at their 60s/512MB ceiling), 2GB S3 storage, 2,000 PUT/10,000 GET, 5,000 DynamoDB write/10,000 read units, 1GB table storage, 1GB logs ingested/stored, 1,000 model calls at 5,000 input/1,000 output tokens, 400 messages and 2,000 transitions totals **$2.191609**. This is a workload example, not a cap or forecast. Image tokenization, notice/analysis runtimes, retries, abuse, data transfer, artifact storage, versions, extra logs and additional resources can raise charges. [AWS pricing](https://aws.amazon.com/pricing/) and [Step Functions pricing](https://aws.amazon.com/step-functions/pricing/) remain authoritative; refresh for materially different workloads. The hourly schedule runs without browser traffic; retained data and logs cost money after demo/stack deletion.

## Failure handling and rollback

Timebox nonessential integration troubleshooting to 10–15 minutes. Preserve evidence and diagnose the actual failing resource rather than repeatedly redeploying or invoking billable models.

1. Authentication/expired CLI cache: user refreshes `aws login --profile hackathon` in a writable normal terminal, then reverify STS. Do not alter default/MCP credentials.
2. AccessDenied after previously working operations: check project spend status in AWS Settings > Billing, plan/service availability and SCP/RCP restrictions. Never widen IAM or move Regions blindly.
3. Failed stack: inspect `aws cloudformation describe-stack-events --profile hackathon --region ap-southeast-2 --stack-name argus` for resource failure chronology. Use `aws cloudformation describe-events --profile hackathon --region ap-southeast-2 --stack-name argus` where available for service pre-deployment validation findings. Identify actionable failure before retrying.
4. Runtime error: resolve the function's actual physical ID from `describe-stack-resources`, then read its Sydney `/aws/lambda/<physical-id>` log group with `aws logs tail ... --since 10m`. If no logs, diagnose scoped logging permission using the actual ARN; the simulator limitation is not permission to grant blanket logs access.
5. SES sandbox/rate limit: preserve dry-run inbox and bounded tests; no production access request or external-recipient sends without approval.
6. Bedrock AccessDenied/schema error: verify regional model permissions/provider prerequisites and request shape; no listing-based success claim and no global fallback. Keep demo/mock labeling explicit.
7. S3/name conflict or rollback-retained tables: inventory and confirm ownership/stack management. Import/recovery is a separate reviewed plan; never delete retained evidence or duplicate stack-owned resources manually.
8. CORS mismatch: compare browser origin to FrontendOrigin and returned headers; check API_BASE contains exactly one `/v1`. Changing the allowed deployment origin is another SAM change, not an ad hoc resource edit.

CloudFormation default rollback remains enabled. For a later bad update, redeploy the previously reviewed template/artifacts **only with explicit approval**; do not Git-reset the user's working tree. `UPDATE_ROLLBACK_FAILED` requires diagnosed, approved recovery before `continue-update-rollback`. Deleting a stack, stopping executions, disabling a schedule, deleting test objects/records or altering retention are mutations and need authorization. Retained bucket/tables and unmanaged runtime log groups survive stack deletion; artifact resources may survive too. Ask whether to keep or clean up resources after the demo, with a concrete inventory and explicit approval. Never delete evidence to reduce costs automatically.

## Deadline-critical remaining checklist

- Completed: Approval A and B received with exact bounded test scope and acknowledgement of unauthenticated demo exposure.
- Deploy via existing script and inspect actual change set; stop on unexpected replacements or project/Region mismatch.
- Capture real outputs; start frontend with live API and mocks disabled.
- Verify report upload/submission, persistence and case retrieval using disposable data.
- Test regional Bedrock only within approved bounded budget; clearly disclose any fallback or failure.
- Record a stable demo and preserve remaining security/runtime limitations. Authentication, abuse controls, long-term log retention, unpatched dev glob chain, bundle splitting and complete production hardening remain follow-up work.

### First approved deployment finding

The packaging stack reached CREATE_COMPLETE. The first application change set failed early property validation because S3 AllowedOrigins contained duplicate localhost values when FrontendOrigin equaled the default. No application resources were created by that failed change set. The template now conditionally omits the second localhost entry when redundant, for both API and S3 CORS. Nine infrastructure tests pass, including both local and distinct hosted-origin configurations. The approved retry completed successfully; validation was not bypassed.

### Sandbox credential refresh correction

SAM SDK refresh required a writable login cache even after the normal-terminal login succeeded. The existing hackathon login cache entry alone was copied into ignored `.cache/aws-login/` (directory 0700, file 0600), using its configured login_session cache key. Setting AWS_LOGIN_CACHE_DIRECTORY per process allows normal refresh without changing global credentials/configuration. Treat this cache as sensitive runtime state; never archive, stage, print or upload it. Use this environment variable for SDK/CLI deployment and seeding in this sandbox. The corrected change set passed service validation: 53 additions, zero deletions/replacements; execution was confirmed under the existing user approval.

### Approved live checkpoint and targeted repairs

Initial stack CREATE_COMPLETE; ApiBase is https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1. Five live read smoke checks passed. Eight assets and three explicitly seeded illustrative cases were written under the approved seed allowance. The frontend serves live data at localhost:5173 with mocks disabled and a visible OpenStreetMap fallback. MapLibre 6 requires an explicitly Vite-bundled worker URL; this is now configured and production build emits its worker asset.

The first browser upload did not reach analysis because the prior presigner used a global S3 hostname and Signature V2. Upload/evidence presign clients now explicitly use Sydney endpoints and Signature V4. A real SDK test verifies the URL host and signing scope without AWS requests. Importing actual SAM handlers revealed Cases imported road_for_point from the wrong shared module; that import is fixed and all 14 real handlers now import. The state machine physical name is EscalationStateMachine-RhE2OhCiVV69, without an argus prefix; its trust boundary now uses the actual SAM logical-name family, restricted to this project and Sydney. The reviewed SAM code/trust update reached UPDATE_COMPLETE, without bucket/table/state-machine replacement. Live outcomes are recorded below.

### Verified deadline demo checkpoint

Actual outputs are recorded in INTEGRATION_HANDOFF.md. API: https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1. Frontend: http://localhost:5173 (local server, actual AWS backend). DEMO_RUNBOOK.md contains exact startup/check commands and a recording sequence. No frontend hosting resources were provisioned.

One disposable Argus-logo image upload returned 200; POST /cases returned 201 with CS-BNEZAQ. Photo key persisted; browser Cases retrieval after reload passed at 1440px with no page errors. Existing seeded rows' invalid jurisdiction/warranty metadata was repaired with conditional updates to three seed IDs only; a targeted contract test passed. No fabricated successful API responses or model analysis.

Regional Nova Lite Converse was denied by AWS because this project is undergoing verification (AWS says normally under two hours). Do not repeatedly invoke, loosen permissions or route cross-Region. Deployed USE_MOCKS remains false; the existing manual report path and identified notice template fallback were used. Exactly one SES notice was accepted to the verified dry-run inbox; mailbox delivery unverified.

DescribeExecution found the demo execution FAILED/States.Runtime at NextRung: timeout Catch default ResultPath replaced the input, losing $.rung. Both timeout and ClosureRejected catches now retain context at $.wait_error. A targeted regression test passed. The failed execution is preserved, and CS-BNEZAQ remains AWAITING_FIX; do not imply an active successful escalation or verified closure. The targeted SAM update reached UPDATE_COMPLETE at approximately 18:35 IST, without data-resource replacement or new privilege grants. AWS DescribeStateMachine confirms ACTIVE with both catches using $.wait_error. SAM retired the previous unused shared layer version during normal update cleanup; no evidence/data was deleted. No new case/restarted execution/additional test emails are authorized implicitly by this fix.

Latest full backend run: 82 passed; subsequent seed-contract and workflow-context targeted checks each passed. Existing frontend TypeScript, 17 Vitest tests, 12 API runtime checks and worker-aware production build passed. SAM lint/build passed again for the workflow change. No redundant full suite, optional guard expansion, UI redesign or unrelated dependency upgrade was performed. Production npm audit remains clean; five high development-only glob advisories remain assessed follow-up work. Whitespace check and SPEC preservation check passed. All work remains uncommitted on feat/aws-integration.

Final deployment status: **UPDATE_COMPLETE**. No CloudFormation operation remains running. The existing frontend server remains available for recording. Keep resources for the submission; cleanup is deferred and requires separate authorization.
