# Shared backend handoff — Argus Web

Verified 2026-10-11 in project **262952461520**, profile **hackathon**, Region **ap-southeast-2**. SAM stack `argus` is UPDATE_COMPLETE, including the timeout-context correction. Argus Mobile was not accessed or tested.

| Value | Verified configuration |
|---|---|
| ApiBase / VITE_API_BASE | https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1 |
| VITE_AWS_REGION | ap-southeast-2 |
| VITE_USE_MOCKS | false |
| VITE_LOCATION_API_KEY | Leave empty for the working OpenStreetMap fallback; AWS Location key not provisioned |
| BucketName | argus-262952461520-ap-southeast-2 |
| AssetsTableName | argus-Assets |
| CasesTableName | argus-Cases |
| CaseEventsTableName | argus-CaseEvents |
| StateMachineArn | arn:aws:states:ap-southeast-2:262952461520:stateMachine:EscalationStateMachine-RhE2OhCiVV69 |
| CORS | Browser origin http://localhost:5173; API GET/POST/OPTIONS; storage GET/PUT/HEAD |
| Contract | contracts/openapi.yaml; includes /v1 exactly once in ApiBase |

## Verified live behavior

Five read smoke checks passed: health, hotspots, risk, assets and evaluation response shape. Browser renders actual map tiles and live API hotspots. One disposable Argus-logo image uploaded through a Sydney Signature V4 presigned URL (HTTP 200); one manual report created **CS-BNEZAQ** (HTTP 201), persisted its photo key and was retrieved in Cases after a browser reload, with no page errors. The uploaded logo is test evidence, not a real hazard photograph. Three older cases carry SEED labels; their events/evaluation results are illustrative. Seed jurisdiction/warranty metadata was repaired without overwriting case history.

SES accepted a dry-run message to the verified sender/inbox **chauhanansh1046@gmail.com**; mailbox delivery was not checked. SES is in sandbox. Notice text used the existing template fallback, explicitly identified in event metadata.

Actual regional Nova Lite Converse invocation was denied because AWS says the project is undergoing verification, normally under two hours. No successful AI inference is claimed. Keep amazon.nova-lite-v1:0 and deployed USE_MOCKS=false; do not substitute a global/cross-Region profile. Manual submission remains available.

The demo escalation execution failed at NextRung because a caught timeout replaced its input. The targeted ASL correction preserves context under $.wait_error for timeout/rejected closure. The failed execution is retained; do not claim the complete four-rung workflow passed or restart it without checking remaining test authorization. The correction is deployed and its active ASL definition was verified; a new complete escalation execution was not tested.

## Integration limitations and security

API is temporarily unauthenticated under explicit demo approval; CORS is not authorization. No public frontend hosting was deployed. Web runs at http://localhost:5173 against the real AWS API. VITE_* values are public: never include AWS credentials, PATs or private tokens. Do not publish presigned URLs or workflow task tokens. Bucket/table retention protects evidence; no automatic upload expiration. Hourly scoring remains active and may incur charges even when the browser is closed.

No mobile, physical-device, PWA installation, successful model evaluation or verified closure claim is warranted. Production authentication/abuse controls, log retention and five high development-only glob dependency advisories remain follow-up work; production npm audit has no findings. Existing architecture and features remain intact.
