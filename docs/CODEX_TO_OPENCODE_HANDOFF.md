# Argus Web handoff: Codex to OpenCode

**Prepared:** 2026-10-11
**Purpose:** Preserve the current state and transfer the five locally implemented functional fixes for review and deployment. This is a handoff only: no AWS operation, Amplify publication, commit, or push was performed for these fixes.

## Repository state

- Repository: `/home/ansh/Projects/argus-aws/argus`
- Branch: `feat/aws-integration`
- HEAD: `d98fb97bff03e2e013ed6615a82a8abce6a8c6fb` (`feat: deploy and integrate Argus Web with AWS backend`, 2026-10-11)
- Remote: `origin https://github.com/argus-zest/argus` (fetch and push)
- Working tree: dirty, with 30 paths total (26 modified tracked files and 4 untracked files, including this handoff). Before creating this handoff, 29 paths were already dirty. Do not discard or rearrange changes before reviewing them. `SPEC.md` is unchanged. No commit or push was made.

Changed tracked files:

```text
backend/functions/analyze/app.py
backend/functions/claim_fix/app.py
backend/layer/python/common/notice_template.py
backend/layer/python/common/nova.py
contracts/openapi.yaml
contracts/schemas/HazardAnalysis.json
docs/AWS_EXECUTION_HANDOFF.md
docs/DEPLOYMENT_PLAN.md
docs/DEPLOYMENT_READINESS.md
docs/HUMAN_TODO.md
frontend/src/App.tsx
frontend/src/components/CasesModal.tsx
frontend/src/components/MapView.tsx
frontend/src/components/Navbar.tsx
frontend/src/components/ReportModal.tsx
frontend/src/components/RightPanel.tsx
frontend/src/lib/api.ts
frontend/src/lib/response-schemas.ts
frontend/src/lib/types.ts
frontend/src/test/api-client.test.ts
samconfig.toml
scripts/deploy.sh
template.yaml
tests/test_infrastructure_guards.py
tests/test_phase4.py
tests/test_phase5.py
```

Untracked files:

```text
docs/CODEX_TO_OPENCODE_HANDOFF.md
docs/FRONTEND_DEPLOYMENT.md
frontend/src/lib/map-config.ts
frontend/src/test/map-config.test.ts
```

The pre-existing dirty paths from before the five bug fixes are `docs/AWS_EXECUTION_HANDOFF.md`, `docs/DEPLOYMENT_PLAN.md`, `docs/DEPLOYMENT_READINESS.md`, `docs/HUMAN_TODO.md`, `samconfig.toml`, `scripts/deploy.sh`, `template.yaml`, `tests/test_infrastructure_guards.py`, and the untracked `docs/FRONTEND_DEPLOYMENT.md`. They include earlier deployment/CORS/configuration work and must be preserved. The remaining changed files and three untracked map/test files are the functional-fix work from this session. Inspect diffs before staging anything.

## Application and AWS environment

Argus Web is a React 18 + TypeScript + Vite SPA using MapLibre and Tailwind. The browser calls a public API Gateway HTTP API; API operations are served by Python 3.12 Lambda functions. The backend uses a shared Python Lambda layer, S3 presigned uploads and evidence storage, DynamoDB case/asset/event tables, Step Functions escalation, EventBridge scheduling, regional Bedrock Nova Lite, and SES dry-run notices. The SAM template is `template.yaml`; the contract is `contracts/openapi.yaml` plus `contracts/schemas/`.

Known environment:

| Item | Value / status |
|---|---|
| AWS project/account ID | `262952461520` |
| AWS CLI profile | `hackathon` |
| Previously verified role | `AccountFullAccessRole` |
| Assigned Region | `ap-southeast-2` only |
| CloudFormation stack | `argus` |
| Public frontend | <https://demo.d1ygq6l84twsei.amplifyapp.com> |
| Amplify app | `argus-web-hackathon`; manual artifact hosting in `ap-southeast-2` (Amplify’s delivery uses global CloudFront, allowed by project guidance) |
| API base | `https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1` |
| Verified demo case | `CS-BNEZAQ` |
| Frontend region | `VITE_AWS_REGION=ap-southeast-2` |
| Backend model | `amazon.nova-lite-v1:0`, explicit in-Region model; no global inference profile |
| Frontend mock mode | `VITE_USE_MOCKS=false` for live use; mock fixtures are read-only and visibly identified |

The AWS CLI profile was previously verified against project `262952461520` in `ap-southeast-2`. Reverify with `aws sts get-caller-identity --profile hackathon --region ap-southeast-2` before any AWS operation. Historical AWS MCP config used `AWS_MCP_PROXY_PROFILES=default`; do **not** assume MCP and `hackathon` use the same identity. If using MCP, verify its caller identity independently and stop if it differs. Do not edit global credentials or OpenCode configuration to resolve a mismatch without explicit authorization.

The last known hosted site had live API access after an approved CORS stack update. Existing API and S3 CORS should allow exactly `http://localhost:5173` and `https://demo.d1ygq6l84twsei.amplifyapp.com`; the API methods are GET/POST/OPTIONS and S3 upload methods GET/PUT/HEAD. Confirm from AWS/read-only browser evidence before claiming current status. The CORS/Region edits in the local `template.yaml` are among the pre-existing uncommitted changes.

SAM defines one HTTP API, one shared Lambda layer, a retained S3 evidence bucket (`argus-${AWS::AccountId}-ap-southeast-2`) and bucket policy, three PAY_PER_REQUEST DynamoDB tables, 14 Lambda functions, 15 execution roles, a Standard Step Functions state machine, and an hourly EventBridge schedule. Function logical IDs are Health, Hotspots, Risk, Assets, EvalResults, ScheduledScore, Presign, Analyze, TenderClause, Cases, ClaimFix, RegisterToken, MarkClosed, and NoticeAgent. API integrations/routes and their permissions are SAM-generated. Existing infrastructure is already deployed; do not recreate it.

## Five functional fixes now present locally

These implementations have **not** been published to Amplify or deployed to the Lambda backend. Preserve all five; review the diffs before any edits.

1. **Daily Bedrock quota and manual reports.** `backend/layer/python/common/nova.py` configures a single SDK attempt so Bedrock daily token-cap `ThrottlingException`s can be distinguished from transient throttling. A transient throttle may be retried once; a daily cap is not retried. Errors use safe messages and logs include diagnostic code/request ID rather than prompt, image, or raw exception content. `backend/functions/analyze/app.py` maps these to friendly 503s. `frontend/src/components/ReportModal.tsx` retains a successfully uploaded image/S3 key, labels analysis unavailable, and keeps manual report creation available where supported. No fake assessment is returned.

2. **Map at high zoom.** `frontend/src/components/MapView.tsx` used an OSM raster style layer with `maxzoom: 19` while the map itself could zoom to MapLibre’s higher default. At the source boundary, the layer disappeared as navigation continued. `frontend/src/lib/map-config.ts` sets the source/map ceiling to z=19; the style layer no longer hides at z=19. `frontend/src/test/map-config.test.ts` guards the shared limit. Browser tests also exercised the actual zoom control.

3. **Photo assessment provenance and fabricated fallback.** New manual photo submissions previously created a synthetic `unclear`/severity 3 assessment when analysis failed. UI and dry-run notice paths also displayed default hazard/severity values. `frontend/src/components/ReportModal.tsx` now sends analysis only after a valid response and labels Bedrock severity as AI-estimated; unavailable inference keeps the photo and omits assessment. `frontend/src/components/CasesModal.tsx` distinguishes Bedrock, local mock, unknown-source, unavailable, and recognized legacy fallback data. `backend/layer/python/common/notice_template.py` avoids inventing severity and labels mock/unavailable analysis; legacy fabricated manual fallback data is called out. `backend/layer/python/common/nova.py` validates required fields and throws a classified error for malformed responses rather than manufacturing an `unclear` result. `contracts/schemas/HazardAnalysis.json` records optional `source` provenance; frontend analysis/case types carry that source.

4. **Reopen right sidebar.** `frontend/src/components/RightPanel.tsx` gives the close control an accessible name. `frontend/src/components/Navbar.tsx` exposes an always-visible “Details”/panel icon control while closed, wired through `frontend/src/App.tsx`. No sidebar content or animation branch was changed.

5. **Repair claim contract and status.** Backend deterministic prechecks return `verification: null`, but the frontend contract required a verification object and threw `Invalid API field: response.verification`. `frontend/src/lib/response-schemas.ts`, `frontend/src/lib/types.ts`, and `frontend/src/lib/api.ts` accept nullable verification and safely read nested explanation. `contracts/openapi.yaml` documents nullable verification, 409/503 outcomes, and the Analyze 503; `backend/functions/claim_fix/app.py` requires original and after-repair images, keeps proximity validation, maps unavailable model inference to 503 without updating case/events/Step Functions, and handles image formats from file extensions. `backend/layer/python/common/nova.py` rejects incomplete/malformed verification. The UI represents transport/dependency/unavailable outcomes as pending, not a verified rejection; only an actual backend `accepted: false` result is shown as a rejection. It cannot close without backend confirmation. Regression cases are in `tests/test_phase4.py`, `tests/test_phase5.py`, and `frontend/src/test/api-client.test.ts`.

The Cases modal also now has an expandable explanation of the configured escalation ladder. It states rung 1 assigned agency officer, rung 2 Flood Control Order nodal officer, rung 3 owning agency Superintending/Chief Engineer, rung 4 District Magistrate; advances on timer expiry or an actually rejected repair verification; demo timers 20 seconds per rung; real timers 3/2/2/3 days; final unresolved state. This is frontend-only and does not change the workflow definition.

## Validation checkpoint

The following are the last successful checks for the current local implementation, after the contract correction and strict location-comparison validation:

- `pytest -q tests/test_phase4.py tests/test_phase5.py tests/test_phase6.py tests/test_local_nova_mocks.py tests/test_workflow_context.py`: **37 passed**.
- From `frontend/`, `npm test`: **19 passed across 3 files**.
- From `frontend/`, `npm run build`: passed TypeScript (`tsc`) and Vite production build. Vite reports the existing large main JS chunk (>500 KB; no build failure).
- From `frontend/`, `npm run test:api`: **12 passed**.
- `NPM_CONFIG_CACHE=/tmp/argus-npm-cache npx --yes @redocly/cli lint contracts/openapi.yaml`: passed; OpenAPI is valid. The first attempt using the default read-only npm cache failed with EROFS; rerun succeeded using `/tmp`.
- `sam validate --lint --region ap-southeast-2` and `sam build`: passed in official Docker image `public.ecr.aws/sam/build-python3.12:latest-x86_64`, SAM CLI 1.168.0. No deployment was invoked. SAM’s “requirements.txt file not found” messages were benign for these source-copy functions/layer.
- `git diff --check`: passed.
- Real Chromium with local Vite server at port 5176 and explicit `VITE_USE_MOCKS=true`: at 1440x900 and 390x844 the Details panel closed/reopened twice, map controls stopped at zoom 19, no horizontal overflow, canvas dimensions were 640x770 and 390x464, and no page errors occurred. OSM tile requests were intercepted with synthetic local tiles. This was **not** live backend verification and must not be described as such.
- No new full suite was run; the previously accepted broad checkpoint was 62 backend tests, 19 frontend tests, 12 API checks and a production build, but use the exact targeted count above for the latest current source.

## Current deployed code versus local changes

- Deployed/public baseline remains commit `d98fb97bff03e2e013ed6615a82a8abce6a8c6fb` and is available at the Amplify URL above. The five fixes in this handoff are only in the local dirty worktree.
- The currently deployed Lambda code likewise does not contain the new Bedrock classification, no-fabrication behavior, notice changes, or claim-fix changes. A SAM deployment is needed for those backend changes.
- The local frontend `frontend/dist` was built from these fixes during validation, but the public Amplify app was **not** updated with it. Rebuild with the verified public Vite configuration and publish after approval.
- No live test was performed against the public site after these uncommitted changes. No new report, case, S3 object, email, Bedrock call, stack update, or resource was created in this session.

## Security and functional limits

- Keep all regional operations in `ap-southeast-2`; no cross-Region/global Bedrock inference. Model ID stays `amazon.nova-lite-v1:0`.
- Bedrock project verification previously blocked real inference, and daily token exhaustion was reported. Do not claim real AI results unless a real successful invocation is observed. Do not retry daily quota exhaustion, request quota increase, change models, or route cross-Region.
- Manual photo/report flow remains available after an analysis failure where backend validation allows it. Keep the uploaded original evidence.
- Repair verification requires original and after-repair photos plus the existing geographic proximity gate. A 503/unavailable/malformed model result leaves the claim pending and must not signal case closure or rejection.
- Hosted API endpoints are publicly callable and unauthenticated for the demo; CORS is not authentication. Keep demo data non-sensitive and bounded.
- SES was previously verified for the selected sender/inbox but is in the sandbox; preserve DRY-RUN routing and do not send to officials/external recipients.
- IAM/Access Analyzer findings and any logging-simulation limitations are recorded in the existing deployment handoff. Do not claim a new security audit from this targeted bug-fix run.

## Deploying the fixes (approval required)

### Backend: SAM/CloudFormation

The code changes in `backend/functions/analyze/app.py`, `backend/functions/claim_fix/app.py`, `backend/layer/python/common/nova.py`, and `backend/layer/python/common/notice_template.py` require a stack update. `Globals.Function.Layers` references `SharedLayer`, so publishing a new layer version may update Lambda layer references/configuration across all 14 functions even though only Analyze, ClaimFix, and NoticeAgent behavior directly uses the modified paths. `SharedLayer` is `AWS::Serverless::LayerVersion` with `RetentionPolicy: Delete`; inspect whether the old immutable published layer version will be removed. This is a code-layer change, not intended persistent-data replacement. No IAM policy edit was introduced by these functional fixes. No DynamoDB table, evidence bucket, state machine, or EventBridge resource should be replaced/deleted for them.

**Do not rely on that expectation instead of reviewing the actual change set.** The dirty `template.yaml` also includes earlier CORS updates. Run identity checks, build, and package/change-set creation only under the user's applicable approval. Review every change-set action, especially `Replacement`, IAM policies, `SharedLayer`, `HttpApi`, and S3 CORS. Stop for unexpected Add/Remove, persistent-data replacement, IAM expansion, or unrelated workflow changes. Do not execute a new change set without explicit approval of that exact reviewed change set. Previous approval of older named changesets does not approve this one.

Intended target if separately approved: stack `argus`, profile `hackathon`, Region `ap-southeast-2`, expected project ID `262952461520`; `CAPABILITY_IAM`, `--resolve-s3`; parameters `SesFrom` and `DryRunInbox` set to the already verified identity per existing deployment docs, `NovaModelId=amazon.nova-lite-v1:0`, `EnableTomtom=false` and empty TomTom key. Reverify identity and SES/model prerequisites before creating a new change set. Existing guarded command is in `docs/AWS_EXECUTION_HANDOFF.md` and `scripts/deploy.sh`; inspect actual parameter names/defaults first. Do not invent sender identities or expose credentials.

### Frontend: Amplify Hosting

After a separate explicit frontend publication approval, build the static artifact using only public settings:

```bash
cd /home/ansh/Projects/argus-aws/argus/frontend
npm ci
VITE_API_BASE=https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1 \
VITE_AWS_REGION=ap-southeast-2 VITE_USE_MOCKS=false VITE_LOCATION_API_KEY= \
npm run build
```

Review `frontend/dist`, then use the existing Amplify app `argus-web-hackathon` in `ap-southeast-2` and its manual artifact deployment flow (Amplify Console: choose the existing app/branch deployment and upload the built static artifact, preserving the configured SPA 200 rewrite). Do not create a second app or modify GitHub integration. Check `docs/FRONTEND_DEPLOYMENT.md` for existing deployment details. Confirm HTTPS, correct public env values, API CORS, hotspot/risk reads, and case retrieval after publish. AWS credentials are needed by the operator doing an Amplify Console/CLI deployment, never by the teammate or embedded frontend.

## Existing documentation to read

1. `docs/AWS_EXECUTION_HANDOFF.md` — authoritative long deployment/security record and approved resource context; note historical sections can mention earlier checkpoints.
2. `docs/FRONTEND_DEPLOYMENT.md` — Amplify artifact/configuration, CORS, prior public browser/live API checks.
3. `docs/INTEGRATION_HANDOFF.md` — public API/frontend environment and verified integration limitations.
4. `docs/DEPLOYMENT_PLAN.md` and `docs/DEPLOYMENT_READINESS.md` — earlier deployment requirements/findings; some statements are historical and can conflict with later successful deployment records.
5. `docs/DECISIONS.md` — Region override, regional Nova Lite, mock restrictions, storage retention, IAM and prior design decisions.
6. `docs/DEPLOYMENT_READINESS.md`, `docs/LOCAL_VALIDATION.md`, and `docs/DEMO_RUNBOOK.md` for local checks and honest demo behavior.

Treat fresh Git status, actual AWS readback, and the latest reviewed CloudFormation change set as authoritative over stale HEAD/branch/status snapshots embedded in older documents. Do not edit `SPEC.md`.

## Exact next actions, in order

1. In OpenCode, confirm cwd is `/home/ansh/Projects/argus-aws/argus`, branch is `feat/aws-integration`, HEAD is still `d98fb97bff03e2e013ed6615a82a8abce6a8c6fb`, and inspect all 30 dirty paths. Preserve all files; do not reset, clean, stash, switch branches, or overwrite the teammate branch.
2. Read this handoff and `docs/AWS_EXECUTION_HANDOFF.md`; reconcile outdated status text without rewriting unrelated documentation. Review the full five-fix source/test diffs, especially model parsing and claim status transitions.
3. If changing code, rerun targeted backend tests, frontend Vitest/API checks, TypeScript/Vite build, OpenAPI lint, `git diff --check`, and SAM lint/build. Current passes and exact scope are above.
4. Obtain current explicit permission for backend packaging/change-set creation/deployment and frontend artifact publication. Before any AWS operation independently verify `hackathon` with STS in `ap-southeast-2` and confirm project ID `262952461520`; if using MCP verify its identity separately from `default` profile.
5. Prepare one SAM change set for the reviewed local template and code. Review all changes/replacements/IAM and persistent resources; present it and wait for approval of that exact change set. Do not bypass CloudFormation or provision resources manually.
6. Once the exact SAM change set is approved, execute only it; wait for a successful terminal stack state. On unexpected replacement/deletion/IAM widening, stop and report; do not auto-retry.
7. Once frontend publication is approved, publish the `frontend/dist` artifact to existing Amplify Hosting with `VITE_USE_MOCKS=false`; preserve the exact production URL and SPA configuration.
8. Smoke-test API CORS, manual report/upload only if separately within approved write scope, a read-only case fetch for `CS-BNEZAQ`, and browser UI. Recheck both localhost and public origin. Avoid Bedrock invocation after daily quota exhaustion unless the user authorizes a bounded retry after quota becomes available. Distinguish local mock/browser checks from live AWS evidence.
9. Report which backend/frontend artifacts were deployed, exact commit/worktree state (no automatic commit/push), stack result, public URL, live verification evidence, and remaining Bedrock/escalation limitations.

## Prohibitions

- Do not access or modify `argus-mobile/`; another session owns it.
- Do not switch branches, merge animation work, commit, or push without explicit instruction. Preserve all current uncommitted work.
- Do not reset, clean, stash, or rewrite Git history.
- Do not deploy, create/update/delete AWS resources, execute a CloudFormation change set, or publish Amplify without the required explicit approval. Never treat an older approval as approval for a new change set.
- Do not modify IAM, request Bedrock quota, send real SES messages, write test reports/cases, or upload/delete evidence without explicit bounded authorization.
- Do not use `us-east-1` for regional resources or use cross-Region inference. Do not turn mocks on in production, fabricate successful API/model responses, or describe mocks as live integrations.
- Do not expose PATs, AWS credentials, session data, presigned URLs, task tokens, or private user data.
- Do not install unrelated tools or update Impeccable. Do not modify `SPEC.md`.
