# Technical Decisions Log (docs/DECISIONS.md)

Record of decisions made where not explicitly specified in `SPEC.md`:

1. 2026-10-10: Used Python 3.12 with standard library `unittest.mock` for local test mocking of AWS services.
2. 2026-10-10: Configured pytest to find backend common layers via `pythonpath = backend/layer/python`.
3. 2026-10-10: Placed `/resolve` route in `backend/functions/hotspots/app.py` as a second route handler to optimize deployment footprint while strictly upholding contract schemas.
4. 2026-10-10: Used `AGENT_BACKEND=converse` tool loop pattern for Bedrock Nova notice generation with guaranteed fallback to `notice_template.py` per Section 15.
5. 2026-10-10: Configured Vitest in `frontend/vitest.config.ts` with `css: false` for lean unit test execution.
6. 2026-10-10: Used Canvas 2D particle simulation for map rain overlay up to 300 streaks to ensure 60fps rendering without WebGL shader overhead.
7. 2026-10-11: Overrode the SPEC Region with ap-southeast-2 per AGENTS.md project Region constraint (project assigned to ap-southeast-2 via settings.aws.com; all Regional resources must be in assigned Region).
8. 2026-10-11: Replaced Nova 2 Lite global inference with regional-only Nova Lite (`amazon.nova-lite-v1:0`); AWS documents Nova 2 Lite as unavailable In-Region in Sydney while Nova Lite supports In-Region inference there. Cross-Region inference is disallowed by project constraints.
9. 2026-10-11: Removed blanket 14-day uploads expiration because persistent case evidence remains under uploads/; enabled explicit S3 encryption/versioning and retain policies for the bucket and DynamoDB tables. Expiration requires a reviewed separation of temporary objects from evidence.
10. 2026-10-11: Deployment requires the hackathon profile, Sydney Region, independently verified project ID, regional Nova Lite, and verified SES sender/inbox. Removed example SES deployment defaults; MCP identity must match hackathon before any MCP provisioning.
11. 2026-10-11: Restored omitted frontend API/type modules using the contract, handlers, and UI tests; added a gitignore exception for frontend/src/lib. API adapters validate response fields, normalize traffic percent to a fraction, and reject failed uploads before downstream analysis.
12. 2026-10-11: Implemented explicitly marked conservative local inference fixtures behind USE_MOCKS=true and ARGUS_ENV=local; deployed Lambda cannot use them. Fixtures never verify closure or fabricate tender quotes/evaluation metrics. Frontend fixtures remain development-only and read-only; storage, workflows, persistence, and email are not mocked by these flags.
13. 2026-10-11: Added an S3 deny policy for insecure application transport covering bucket and objects, exempting direct AWS service principals whose network context can be redacted. Kept evidence encryption, versioning, and retention; SES identity-policy tightening awaits deterministic analysis and all infrastructure changes await deployment approval.

- 2026-10-11: Remediated production MapLibre attribution vulnerability with 6.4.1; validated required major dependency updates (Vite 6.4.3, Vitest 4.1.11), retained Tailwind 3 with patched parser override, and documented five unpatched development-only braces-chain findings.
- 2026-10-11: Replaced broad SAM policy templates with 15 source-reviewed execution roles, exact Sydney Nova Lite and SES sender/dry-run recipient constraints, S3 prefix access and table/workflow scoping; Access Analyzer passed, with logging simulation limitation explicitly recorded.
- 2026-10-11: Corrected narrow Web panel/navigation/case-detail layout without changing animation behavior; created AWS_EXECUTION_HANDOFF.md as the authoritative approval-gated deployment and demo plan.
