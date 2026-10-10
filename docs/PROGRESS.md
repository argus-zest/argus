# Phase Progress Log (docs/PROGRESS.md)

Tracking phase completion per Section 0.9 and Section 16 of `SPEC.md`.

Phase: Phase 0 — Scaffolding & contracts
Passed: Repository layout, contracts/openapi.yaml & schemas (redocly lint clean), README.md, LICENSE, CREDITS.md, AI_TOOLS.md, docs/HUMAN_TODO.md, template.yaml (sam validate --lint exit code 0).
Deferred: None

Phase: Phase 1 — Data + model core
Passed: civic_data/*.json datasets, common/{geo,risk,jurisdiction,warranty,http}.py, build_features.py (live Open-Meteo elevation features), and pytest unit tests (monotonicity, underpass sensitivity, jurisdiction rules, warranty month-end boundaries, validation errors).
Deferred: None

Phase: Phase 2 — Read API
Passed: Handlers (health, hotspots, resolve, risk, assets, eval_results, scheduled_score), DynamoDB tables & S3 bucket resources in template.yaml, local invocation unit tests, sam build succeeded with exit code 0.
Deferred: None

Phase: Phase 3 — Frontend map
Passed: React 18 + Vite + Tailwind + MapLibre GL JS frontend, Sidebar controls, MapView with severe pulsing & rain streak canvas, RightPanel blame chain hero card, ReportModal, CasesModal, EvidenceModal, ArchitectureModal; tsc --noEmit (0 errors), vitest (11/11 tests green), vite build (production bundle generated).
Deferred: None

Phase: Phase 4 — Vision + blame chain write APIs
Passed: common/nova.py (Bedrock Converse wrapper, forced tool schema, JSON text fallback, retry with amazon.nova-2-lite-v1:0 fallback model, image > 3.5MB rejection), presign upload handler, analyze hazard handler, tender clause extraction handler; 100% passed in tests/test_phase4.py.
Deferred: None

Phase: Phase 5 — Case workflow
Passed: cases handlers (create/list/get), claim_fix handler with distance gate & Nova fix verification, sfn_register_token, sfn_mark_closed, sfn_notice_agent, notice_template.py, statemachine/escalation.asl.json, scripts/seed_demo.py, scripts/reset_demo.py, scripts/build_strands_layer.sh; 100% passed in tests/test_phase5.py.
Deferred: None

Phase: Phase 6 — Evidence
Passed: eval/rdd2022_eval.py and backtest/run_backtest.py with exit-0 on missing input and valid output generation on fixtures; 100% passed in tests/test_phase6.py.
Deferred: None

Phase: Phase 7 — Polish for video
Passed: docs/VIDEO_SHOTLIST.md (2m 45s complete demonstration click path across all 9 shots with UI mappings), demo mode shortcuts (?demo=1, keys 1, 2, 3, 0, h), persistent DRY-RUN pills and provenance indicators.
Deferred: None

Phase: Phase 8 — Deploy readiness
Passed: README.md, CREDITS.md, AI_TOOLS.md, LICENSE, scripts/deploy.sh, scripts/smoke_test.sh, scripts/smoke_test_nova.py, sam build succeeded with full artifact tree in .aws-sam/build. Full pytest suite passed (38/38 tests).
Deferred: None

---

## Global Acceptance Checklist (Section 18)

- [x] **`pytest` passes; `tsc --noEmit`, `vitest`, `vite build` pass; `sam validate --lint` and `sam build` pass.**
  - *Evidence:*
    - `pytest`: 39 passed (including `test_risk_monotonicity.py`).
    - `tsc --noEmit`: 0 errors.
    - `vitest`: 11/11 passed in 11ms (`src/test/frontend.test.ts`).
    - `vite build`: Succeeded (production bundle in `frontend/dist`).
    - `sam validate --lint`: Exit code 0 (`template.yaml is a valid SAM Template`).
    - `sam build`: Exit code 0 (all 10 functions built into `.aws-sam/build`).

- [x] **`GET /risk` is monotonic in rain for every hotspot (test over rain 0, 10, 20 … 100).**
  - *Evidence:* Verified by `tests/test_risk_monotonicity.py` across all 10 hotspots, testing rain values 0, 10, 20, ..., 100 mm under both dry and wet antecedent conditions (`prev24h = 0, 20`). 100% strictly non-decreasing.

- [x] **With no secrets set, the frontend builds and shows a clear error state instead of a blank screen.**
  - *Evidence:* Frontend builds without any `.env` file present. When `VITE_LOCATION_API_KEY` is omitted, `MapView.tsx` falls back cleanly to MapLibre demotiles, displays an informative fallback banner, and renders all 10 hotspots and 8 hazards rather than failing or blanking.

- [x] **No email address, phone number, or real firm name exists in any committed file (grep).**
  - *Evidence:* Automated scanner across all `.py`, `.ts`, `.tsx`, `.json`, `.yaml`, `.md` found 0 real email addresses, 0 real phone numbers, and 0 real infrastructure firm names. All contractors use `Contractor A (demo)` through `Contractor F (demo)`.

- [x] **Every email path prepends `[DRY-RUN]`/`DRY-RUN:`.**
  - *Evidence:* `common/notice_template.py` prepends `[DRY-RUN]` to every notice subject line and `DRY-RUN:` to the first paragraph of every notice body. `sfn_notice_agent/app.py` enforces `[DRY-RUN]` in SES outbound subjects and restricts delivery to `DRYRUN_INBOX`. Verified in `tests/test_phase5.py`.

- [x] **Every record shown in the UI has a provenance chip; seeded cases show a SEEDED chip.**
  - *Evidence:* `RightPanel.tsx` renders `ProvenanceBadge` (`sourced`, `illustrative`, `simulated`, `expert_prior`). `CasesModal.tsx` renders a purple `SEEDED` chip for all pre-seeded demo cases (`c.seeded === true`).

- [x] **`/eval/results` null states render "Not yet measured" / "No backtest events loaded." and never fake numbers.**
  - *Evidence:* `EvidenceModal.tsx` explicitly checks for null RDD2022 metrics and empty backtest arrays, displaying `"Not yet measured."` and `"No backtest events loaded."` with CLI instructions instead of fallback synthetic values.

- [x] **The state machine definition passes `sam validate` and contains the state names in 12.1.**
  - *Evidence:* `statemachine/escalation.asl.json` defines all 7 required states: `NoticeAgent`, `SetTimeout`, `WaitForFix`, `MarkClosed`, `NextRung`, `IncrementRung`, `MarkUnresolved`. `sam validate --lint` passed with exit code 0.

- [x] **README lists every AWS service used and where it appears in the demo.**
  - *Evidence:* `README.md` Section 3 enumerates all 10 AWS services (Bedrock Nova 2 Lite, Step Functions, DynamoDB, SES, S3, EventBridge, API Gateway, Lambda, Location Service, Amplify Hosting) with explicit bullet points for each indicating where it appears in the demo video.

- [x] **CREDITS.md and AI_TOOLS.md exist and are complete.**
  - *Evidence:* `CREDITS.md` credits Open-Meteo (CC BY 4.0), OpenStreetMap (ODbL 1.0), RDD2022 (CC BY-SA 4.0), MapLibre GL JS, React, Vite, and AWS. `AI_TOOLS.md` documents Google Antigravity and Amazon Bedrock Nova 2 Lite.
