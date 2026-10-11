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
