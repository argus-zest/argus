# SPEC.md — "Argus": waterlogging prediction + hazard accountability platform

You are building a hackathon prototype. Read this ENTIRE file before writing any code. Follow it literally. Where this file gives an exact value, name, path, or schema, use it exactly. Where something is not specified, choose the simplest option that satisfies the Definition of Done and record the choice in `docs/DECISIONS.md` (one line each). Do not ask me questions unless a rule in section 0 says to stop.

Today is 2026-10-10 (Saturday). The submission deadline is 2026-10-11 20:00 IST. Code freeze is 2026-10-11 14:00 IST. Speed matters: a working, deployed, honest prototype beats a broad, half-working one.

---

## 0. Operating rules for you (the agent)

0.1 Work in Planning mode. Produce ONE implementation plan artifact covering Phase 0 only, then proceed autonomously through all phases without waiting for approval. Stop and ask me only if (a) a required AWS action cannot be done by me with the steps in `docs/HUMAN_TODO.md`, or (b) two rules in this file contradict each other.

0.2 You MAY run: local build/test/lint commands, `pip`, `npm`, `sam validate`, `sam build`, `pytest`, `vite build`, and read-only `aws` commands (`aws sts get-caller-identity`, `aws bedrock list-foundation-models`, etc.) with `--profile hackathon --region us-east-1`.
You MUST NOT run: `sam deploy`, `aws ... delete*`, `aws iam ...`, `aws amplify ...`, or any command that creates or changes cloud resources. Instead, write `scripts/deploy.sh` and tell me to run it. Never print, log, or commit credentials, API keys, or `.env` files. Commit only `.env.example`.

0.3 Never invent data. Every number, name, date, clause, email address, or statistic shown in the UI must come from (a) a file in this repo with a `provenance` tag, (b) a live API call, or (c) the user's input. If something is unavailable, the UI shows "Not available" or "Not yet measured". Never fabricate evaluation results.

0.4 Provenance tags. Every data record in `backend/layer/python/civic_data/*.json` has `"provenance"` with exactly one of: `"sourced"` (with a `source_url`), `"illustrative"` (placeholder I must verify), `"simulated"` (generated for demo). The UI renders a small chip with this value wherever such data is displayed. Colors: sourced = green, illustrative = amber, simulated = grey.

0.5 Safety rules that are non-negotiable:
- No real email address of any official is stored anywhere. Recipients are role labels only (e.g. "Executive Engineer, PWD Division (illustrative)"). ALL emails go to the single env var `DRYRUN_INBOX`. Every email subject starts with `[DRY-RUN]`, and every email body begins with the line `DRY-RUN: this notice was NOT sent to any official.`
- No real contractor/firm names anywhere. Use `"Contractor A (demo)"`, `"Contractor B (demo)"`, etc.
- No scraping of government portals. No SMS. No calls to any API not listed in section 2.

0.6 If a service is blocked, you may add a mock behind an interface, but: mocks are enabled ONLY when env `USE_MOCKS=true`; the deployed SAM template sets `USE_MOCKS=false`; and the UI shows a red "MOCK DATA" badge whenever a response includes `"mock": true`.

0.7 Verify unfamiliar AWS APIs against current official docs (use the browser). Write what you verified (endpoint shape, model ID, request shape) to `docs/VERIFIED_APIS.md`. If this file disagrees with current docs on an API shape, current docs win; note the difference in `docs/DECISIONS.md`.

0.8 Maintain these files continuously (create in Phase 0, update whenever you add a dependency, dataset, or tool):
- `CREDITS.md`: every third-party library, dataset, and API, with licence and attribution text.
- `AI_TOOLS.md`: list "Google Antigravity" plus anything else I tell you I used.
- `LICENSE`: MIT, copyright "Argus contributors".

0.9 After each phase, run that phase's checks and append a 3-line status to `docs/PROGRESS.md`: phase, what passed, what is deferred. Then continue.

---

## 1. Product definition

**One-liner:** Predict where Delhi streets will waterlog, show which hidden hazards (open manholes, potholes, missing drain covers) sit under that water, identify who owns the street and whether its contractor's warranty is still live, and run an automated escalation workflow until the hazard is verifiably fixed.

**Two halves:**
- **Predict:** map of ~10+ known Delhi waterlogging points ranked by probability under adjustable rain. A ranking, NOT a depth forecast.
- **Enforce:** photo → AI hazard rating → owner agency + contractor + warranty resolution → notice (dry-run) → timed escalation to higher officers → fix claimed with new photo → AI verifies → case closes or reopens and escalates.

**Non-goals (do not build):** user accounts or login, real SMS/email delivery to officials, real-time satellite processing, training a vision model, mobile app, payments, multi-city support, admin dashboard.

**Honesty banner text (show under the map legend, exact text):** "Risk is a relative ranking from an expert-prior model, not a flood-depth forecast. Data tagged 'illustrative' is placeholder and must be verified."

---

## 2. Fixed technical decisions (do not substitute)

| Concern | Decision |
|---|---|
| AWS region (everything) | `us-east-1` |
| AWS CLI profile | `hackathon` |
| IaC | AWS SAM, single `template.yaml` at repo root |
| Backend language | Python 3.12, x86_64, no frameworks (plain Lambda handlers) |
| API | API Gateway HTTP API, stage `$default`, base path `/v1`, CORS enabled for `FrontendOrigin` param and `http://localhost:5173` |
| Frontend | Vite + React 18 + TypeScript + Tailwind CSS + `@tanstack/react-query` + `maplibre-gl` |
| Node | 20 |
| Map | Amazon Location Service maps via MapLibre GL JS, authenticated with an API key (env `VITE_LOCATION_API_KEY`) |
| Geocoding | Amazon Location Places `SearchText` (used only by `scripts/geocode_seed.py`) |
| Vision/LLM | Amazon Bedrock, Amazon Nova 2 Lite, via the Converse API. Model ID in env `NOVA_MODEL_ID`, default `global.amazon.nova-2-lite-v1:0` (the global inference profile, which works from us-east-1). Fallback ID: `amazon.nova-2-lite-v1:0`. |
| Agent framework | Strands Agents (`strands-agents`) with a Bedrock model, in the notice Lambda |
| Workflow | AWS Step Functions Standard |
| Schedule | Amazon EventBridge rule, hourly |
| Email | Amazon SES (sandbox), one verified identity used as both sender (`SES_FROM`) and recipient (`DRYRUN_INBOX`) |
| Storage | DynamoDB (3 tables, on-demand) + S3 (1 bucket) |
| Hosting | AWS Amplify Hosting, manual deployment of the `frontend/dist` zip (I will do this in the console) |
| Rain data | Open-Meteo Forecast API and Archive API (no key) |
| Elevation | Open-Meteo Elevation API (no key) |
| Optional traffic | TomTom Flow Segment Data, ONLY if env `ENABLE_TOMTOM=true` and `TOMTOM_API_KEY` is set. Default OFF. |
| Tests | `pytest` for backend, `vitest` for frontend pure functions, `tsc --noEmit` for types |

---

## 3. Repository layout (create exactly this)

```
/
├─ SPEC.md                      (this file, do not edit)
├─ README.md  LICENSE  CREDITS.md  AI_TOOLS.md  template.yaml  samconfig.toml  pytest.ini  .gitignore  .env.example
├─ contracts/
│  ├─ openapi.yaml              (OpenAPI 3.0.3, every endpoint in section 9)
│  └─ schemas/*.json            (JSON Schema for Hotspot, RiskScore, HazardAnalysis, Case, CaseEvent, Jurisdiction, Warranty)
├─ backend/
│  ├─ layer/python/common/      (shared code: http.py, geo.py, risk.py, jurisdiction.py, warranty.py, nova.py, ddb.py, notice_template.py)
│  ├─ layer/python/civic_data/  (roads.json, hotspots.json, assets.json, contracts.json, model_params.json, legal_refs.json)
│  ├─ layer_strands/            (built by scripts/build_strands_layer.sh; gitignored except the script)
│  └─ functions/
│     ├─ hotspots/  risk/  assets/  presign/  analyze/  cases_create/  cases_get/  cases_list/
│     ├─ claim_fix/  tender_clause/  eval_results/  health/
│     ├─ sfn_register_token/  sfn_notice_agent/  sfn_mark_closed/
│     └─ scheduled_score/
│        (each folder: app.py with `handler(event, context)` and nothing else unless needed)
├─ statemachine/escalation.asl.json
├─ frontend/                    (Vite app)
├─ scripts/
│  ├─ geocode_seed.py  build_features.py  seed_demo.py  reset_demo.py
│  ├─ build_strands_layer.sh  deploy.sh  smoke_test.sh
├─ eval/
│  ├─ rdd2022_eval.py  data/README.md  results/.gitkeep
├─ backtest/
│  ├─ run_backtest.py  events.json  results/.gitkeep
├─ tests/                       (pytest)
└─ docs/
   ├─ DECISIONS.md  PROGRESS.md  VERIFIED_APIS.md  HUMAN_TODO.md  VIDEO_SHOTLIST.md  ARCHITECTURE.md
```

`pytest.ini` must set `pythonpath = backend/layer/python` and `testpaths = tests`.

---

## 4. Data contracts and seed data

### 4.1 `roads.json` (array)
```json
{
  "road_id": "string, snake_case, unique",
  "name": "string",
  "center": {"lat": 0.0, "lng": 0.0},
  "coverage_radius_m": 400,
  "road_class": "national_highway | arterial | collector | local",
  "width_ft": 0,
  "is_national_highway": false,
  "in_ndmc": false,
  "mcd_zone": "string | null",
  "ownership_disputed": false,
  "provenance": "illustrative",
  "source_url": null
}
```

### 4.2 `hotspots.json` (array)
```json
{
  "hotspot_id": "string, unique",
  "name": "string",
  "lat": 0.0, "lng": 0.0,
  "coord_verified": false,
  "road_id": "references roads.json",
  "features": {
    "elev_m": null,
    "depression_m": null,
    "rel_elev_m": null,
    "underpass": false,
    "news_events_count": null
  },
  "provenance": "illustrative",
  "source_url": null
}
```
`features.elev_m`, `depression_m`, `rel_elev_m` are filled by `scripts/build_features.py` (section 6.1). `news_events_count` stays null unless I fill it; null is treated as 0 and marked "missing" in the drivers list.

### 4.3 `assets.json` (array; hazards on the ground)
```json
{
  "asset_id": "string, unique",
  "type": "open_manhole | missing_drain_cover | pothole",
  "severity": 1,
  "lat": 0.0, "lng": 0.0,
  "road_id": "string | null",
  "reference_photo_key": null,
  "provenance": "simulated",
  "seeded": true
}
```
Seed exactly 8 assets, each within 40 m of a seeded hotspot, covering at least 3 hotspots and all three types, with severity 2–5. Mark all `"provenance": "simulated"`.

### 4.4 `contracts.json` (array)
```json
{
  "contract_id": "string",
  "road_id": "string",
  "work_type": "recarpeting | redevelopment | drain_construction",
  "contractor_label": "Contractor A (demo)",
  "completion_date": "YYYY-MM-DD",
  "defect_liability_months": 60,
  "maintenance_clause_text": null,
  "tender_doc_key": null,
  "provenance": "illustrative",
  "source_url": null
}
```
Generate 14 rows covering the 10 seeded roads (and 4 extra) such that, as of 2026-10-11: at least 6 are in warranty, at least 4 are expired, and at least 2 have NO contract row for their road (status "unknown"). Use anonymised labels "Contractor A (demo)" … "Contractor F (demo)". Dates must be absolute ISO strings between 2019-01-01 and 2026-08-31.

### 4.5 `legal_refs.json`
```json
[
 {"ref_id":"flood_control_order_2026","text":"Delhi Flood Control Order 2026: a nodal officer is designated for each identified waterlogging point (citation to be verified by the team).","provenance":"illustrative"},
 {"ref_id":"dm_convening","text":"The District Magistrate may convene agencies on waterlogging points with unclear ownership (citation to be verified by the team).","provenance":"illustrative"}
]
```
Notices may quote these strings and nothing else legal.

### 4.6 Seed hotspots (create exactly these 10; coordinates are APPROXIMATE seeds; `coord_verified` false; all `illustrative`)

| hotspot_id | name | lat | lng | underpass | road_id | road_class | width_ft | is_nh | in_ndmc | disputed |
|---|---|---|---|---|---|---|---|---|---|---|
| minto_bridge | Minto Bridge underpass | 28.6330 | 77.2200 | true | minto_road | arterial | 60 | false | false | false |
| pul_prahladpur | Pul Prahladpur underpass | 28.4940 | 77.2910 | true | mehrauli_badarpur_road | arterial | 80 | false | false | false |
| ring_road_who | Ring Road opp. WHO building | 28.6313 | 77.2406 | false | ring_road_ito | arterial | 100 | false | false | false |
| zakhira_underpass | Zakhira underpass | 28.6623 | 77.1480 | true | rohtak_road_zakhira | arterial | 80 | false | false | true |
| loni_road_golchakkar | Loni Road Golchakkar | 28.6830 | 77.2970 | false | loni_road | collector | 50 | false | false | false |
| jahangirpuri_metro_road | Jahangirpuri Metro Station Road | 28.7255 | 77.1627 | false | jahangirpuri_road | collector | 45 | false | false | false |
| karala_kanjhawala | Karala–Kanjhawala Road | 28.7440 | 77.0530 | false | karala_kanjhawala_road | collector | 40 | false | false | false |
| ito | ITO junction | 28.6286 | 77.2410 | false | vikas_marg_ito | arterial | 90 | false | false | false |
| azad_market | Azad Market underpass | 28.6620 | 77.2110 | true | azad_market_road | collector | 40 | false | false | false |
| moolchand | Moolchand underpass | 28.5683 | 77.2347 | true | ring_road_moolchand | arterial | 100 | false | false | false |

Create the matching 10 `roads.json` entries with `coverage_radius_m` 400, `mcd_zone` set to `"Zone (illustrative)"` where `in_ndmc` is false and the road is not an arterial, else null. The loader must support more than 10 hotspots (I may add rows later); never hard-code 10.

`scripts/geocode_seed.py`: for each hotspot, call Amazon Location Places `SearchText` with `QueryText = "<name>, New Delhi"`, `BiasPosition = [77.2090, 28.6139]`, `MaxResults = 1`, using `LOCATION_API_KEY` from env. Write the result to `backend/layer/python/civic_data/hotspots_geocoded.json` containing `hotspot_id`, `geocoded_lat`, `geocoded_lng`, `distance_from_seed_m`. DO NOT overwrite `hotspots.json`. I review and copy values manually. Exit 0 with a clear message if the key is missing.

---

## 5. Shared backend code (`backend/layer/python/common/`)

Pure functions with no AWS calls except `nova.py` and `ddb.py`. All must be unit-tested.

### 5.1 `geo.py`
`haversine_m(lat1, lng1, lat2, lng2) -> float` (metres, Earth radius 6371008.8). `nearest(items, lat, lng, key=lambda i: (i["lat"], i["lng"]))`.

### 5.2 `risk.py` — exact model (expert-prior, NOT fitted)

`model_params.json` (exact content):
```json
{
  "version": "expert-prior-v1",
  "fitted": false,
  "static": {
    "bias": -2.2,
    "w_depression": 0.9,
    "w_low_rel_elev": 0.8,
    "w_underpass": 1.4,
    "w_news": 0.5,
    "norm": {"depression_m": {"mean": 0.0, "std": 1.0}, "rel_elev_m": {"mean": 0.0, "std": 1.0}}
  },
  "event": {"a_susceptibility": 3.0, "b_rain3h": 1.1, "c_rain24h": 0.5, "d_traffic": 1.0, "bias": -6.5},
  "bands": [[0.0, 0.25, "low"], [0.25, 0.5, "moderate"], [0.5, 0.75, "high"], [0.75, 1.01, "severe"]]
}
```
`scripts/build_features.py` must overwrite `norm.mean`/`norm.std` for both features with the mean/std computed over the hotspot set (std floor 0.1) and keep every other value unchanged.

Formulas (implement exactly; `σ(x)=1/(1+e^-x)`; `clip(z,-3,3)`):
```
z_dep  = clip((depression_m - mean_dep) / std_dep, -3, 3)         # null -> 0
z_low  = clip(-(rel_elev_m - mean_rel) / std_rel, -3, 3)           # null -> 0 ; lower ground => higher
S      = σ(bias + w_depression*z_dep + w_low_rel_elev*z_low + w_underpass*(1 if underpass else 0) + w_news*ln(1+news_events_count_or_0))
logit  = event.bias + a*S + b*ln(1+rain_3h_mm) + c*ln(1+rain_prev24h_mm) + d*traffic_slowdown
P      = σ(logit)
```
`score_hotspot(hotspot, rain_3h_mm, rain_prev24h_mm, traffic_slowdown) -> dict` returns:
```json
{"hotspot_id":"", "susceptibility":0.0, "probability":0.0, "band":"low|moderate|high|severe",
 "drivers":[{"name":"depression","contribution":0.0,"missing":false}, {"name":"low_elevation",...}, {"name":"underpass",...}, {"name":"news_events",...}, {"name":"rain_3h",...}, {"name":"rain_prev24h",...}, {"name":"traffic",...}]}
```
`contribution` of each driver is its additive term in the corresponding logit (static terms are inside S's logit; rain/traffic terms are inside the event logit; `a*S` is reported as a driver named "susceptibility"). Return drivers sorted by absolute contribution descending. Round probabilities to 4 decimals.

Input validation (raise `ValueError`): `0 <= rain_3h_mm <= 200`, `0 <= rain_prev24h_mm <= 300`, `0 <= traffic_slowdown <= 1`.

`hazard_under_water(hotspot, assets, probability)`: sum over assets within 50 m of the hotspot of `base[type] * severity/5` where base = open_manhole 1.0, missing_drain_cover 1.0, pothole 0.5; `weight = min(1.0, sum)`; return `{"score": probability*weight, "weight": weight, "asset_ids": [...]}`.

### 5.3 `jurisdiction.py` — deterministic rules with confidence and reasons

`resolve_jurisdiction(road: dict | None, asset_type: str | None) -> dict`:
```json
{"owner":"NHAI|NDMC|PWD|DJB|MCD|ORPHAN", "confidence":0.0, "reasons":["..."], "start_rung":1,
 "officer_role":"string", "provenance_note":"rules are heuristic; verify"}
```
Apply these rules IN THIS ORDER; first match wins:
1. `road is None` → ORPHAN, confidence 0.30, reason "No road record covers this location", start_rung 4.
2. `road.ownership_disputed` is true → ORPHAN, 0.40, reason "Ownership flagged as disputed", start_rung 4.
3. `road.is_national_highway` → NHAI, 0.90.
4. `road.in_ndmc` → NDMC, 0.85.
5. `asset_type == "open_manhole"` → DJB, 0.70, reason "Sewer manholes are typically Delhi Jal Board assets".
6. `road.width_ft >= 60` → PWD, 0.80, reason "Roads wider than 60 ft are treated as PWD roads".
7. Otherwise → MCD, 0.60.
`start_rung` is 1 except for ORPHAN (4). `officer_role` strings (exact): NHAI → "Project Director, NHAI (illustrative)"; NDMC → "Executive Engineer, NDMC (illustrative)"; PWD → "Executive Engineer, PWD Division (illustrative)"; DJB → "Executive Engineer, DJB (illustrative)"; MCD → "Executive Engineer, MCD Zone (illustrative)"; ORPHAN → "District Magistrate (illustrative)". Reasons always include the rule that fired, plus the road's `name`, `width_ft`, and `road_class` when present.

`road_for_point(roads, lat, lng)`: return the nearest road whose `coverage_radius_m` contains the point (by haversine to `center`), else `None`.

### 5.4 `warranty.py`
`compute_warranty(contract: dict | None, as_of: date) -> dict`:
```json
{"status":"in_warranty|expired|unknown", "contractor_label":"", "completion_date":"", "end_date":"", "days_remaining": 0,
 "work_type":"", "clause_text":null, "tender_doc_key":null, "provenance":""}
```
`end_date = completion_date + defect_liability_months` (calendar months; clamp day to the month's last day). `days_remaining = (end_date - as_of).days` (negative when expired). No contract → status "unknown", other fields null. If multiple contracts match a road, pick the one with the latest `completion_date`.

### 5.5 `nova.py` — Bedrock Converse wrapper
- Use `boto3.client("bedrock-runtime", region_name="us-east-1")`.
- `converse(messages, system, tool_config=None, max_tokens=800, temperature=0.1)`. Try `NOVA_MODEL_ID`; on `ValidationException`/`AccessDeniedException`/`ResourceNotFoundException`, retry ONCE with `amazon.nova-2-lite-v1:0`; if that also fails, raise `NovaError(code, message)`.
- `analyze_hazard(image_bytes, fmt) -> HazardAnalysis` using a FORCED tool call: `toolConfig = {"tools":[{"toolSpec":{"name":"report_hazard","description":"Report the road hazard assessment","inputSchema":{"json":{...schema below...}}}}], "toolChoice":{"tool":{"name":"report_hazard"}}}`. If the tool call is missing, fall back to parsing JSON from text; if that also fails, return `{"hazard_type":"unclear","confidence":0,...}`; never raise on parse failure.
  - Schema fields: `hazard_type` (enum `pothole|open_manhole|missing_drain_cover|waterlogging|none|unclear`), `severity` (integer 1–5; 0 when none), `submerged` (boolean), `confidence` (number 0–1), `description` (string ≤ 200 chars), `visible_evidence` (string ≤ 200 chars: what pixels/objects justify the label).
  - System prompt (exact): "You are a road-safety inspector for Delhi. Look ONLY at the image. Report the single most dangerous hazard visible. If you cannot see a clear hazard, use hazard_type 'none' or 'unclear'. Never guess hidden objects: if water covers the road and you cannot see a hole, say so and set submerged true. Be conservative with confidence."
- `verify_fix(before_bytes|None, after_bytes, hazard_type) -> dict` with a forced tool `report_verification` returning `hazard_still_present` (bool), `same_location_plausible` (bool), `confidence` (0–1), `explanation` (≤ 200 chars). If `before_bytes` is None, set `same_location_plausible` from a note in the prompt that no reference photo exists and return `same_location_plausible: null`.
- `extract_clause(pdf_bytes, doc_name)`: send as a Converse `document` block with `format: "pdf"` and `name` sanitised to alphanumerics, spaces, hyphens only. Forced tool `report_clause` returning `found` (bool), `quote` (EXACT verbatim text ≤ 600 chars of the maintenance / defect-liability clause, or empty), `page_hint` (string). System prompt: "Find the clause about maintenance, defect liability, or warranty of bituminous or road work. Copy it VERBATIM. If none exists, found=false. Do not paraphrase."
- Image rules: accept only `jpeg`/`png`; reject > 3.5 MB with `NovaError("IMAGE_TOO_LARGE")`.

### 5.6 `http.py`
`ok(body, status=200)`, `err(status, code, message)` returning API Gateway HTTP API v2 responses with `Content-Type: application/json`. Error body shape (always): `{"error":{"code":"UPPER_SNAKE","message":"human text"}}`. A `parse_json(event)` helper returning a dict or raising `BadRequest`. Every handler wraps its body in try/except; unexpected exceptions return 500 `INTERNAL` with a generic message and log the stack trace to CloudWatch.

### 5.7 `ddb.py`
Thin helpers for the three tables below; convert floats to `Decimal` on write and back on read.

### 5.8 `notice_template.py`
`build_notice(case, rung, kind) -> {"subject","body"}`: deterministic template (see 12.4). This is the guaranteed fallback.

---

## 6. Data scripts

### 6.1 `scripts/build_features.py`
For each hotspot: call Open-Meteo Elevation API (`https://api.open-meteo.com/v1/elevation?latitude=a,b,c&longitude=x,y,z`, max 100 coordinates per call) for: the point; 8 ring points at 200 m (N, NE, E, SE, S, SW, W, NW; use ΔLat = 200/111320, ΔLng = 200/(111320*cos(lat))); and 8 ring points at 1500 m. Compute:
- `elev_m` = elevation at the point
- `depression_m = max(0, mean(ring200) - elev_m)`
- `rel_elev_m = elev_m - mean(ring1500)`
Write values into `hotspots.json` fields (round to 2 decimals), update `model_params.json` norms (5.2), and write `docs/FEATURES_REPORT.md` listing each hotspot's values. Add this caveat to the report verbatim: "Elevation comes from a ~90 m surface model that includes buildings; use as a coarse proxy only." Handle HTTP errors with 3 retries and exponential backoff; if it still fails, leave existing values untouched and exit 1.

### 6.2 `scripts/seed_demo.py` and `scripts/reset_demo.py`
`seed_demo.py` (uses `--profile hackathon`) writes the 8 assets from `assets.json` into the Assets table and 3 seeded cases into the Cases and CaseEvents tables (all with `"seeded": true`):
1. `CS-SEED01`: hotspot `minto_bridge`, status `AWAITING_FIX`, rung 2, 2 events (notice sent rung 1, reminder rung 2).
2. `CS-SEED02`: hotspot `zakhira_underpass` (ORPHAN), status `ESCALATED_DM`, rung 4, 1 event.
3. `CS-SEED03`: hotspot `moolchand`, status `CLOSED_VERIFIED`, rung 1, 3 events (notice, fix claimed, verified).
Seeded cases have `execution_arn: null` and are display-only. `reset_demo.py` deletes ONLY items with `seeded: true` or cases created in the last 24 h whose `demo_run: true`, then re-seeds. Both scripts accept `--dry-run` printing what they'd do.

---

## 7. DynamoDB tables (defined in `template.yaml`, PAY_PER_REQUEST)

- `Assets`: PK `asset_id` (S). Attributes per 4.3 plus `created_at`, `source` (`seed|citizen_report`), `photo_key` (nullable).
- `Cases`: PK `case_id` (S). Attributes: `hotspot_id`, `asset_id`, `lat`, `lng`, `status`, `rung` (N), `owner`, `jurisdiction` (M), `warranty` (M), `analysis` (M), `photo_key`, `execution_arn`, `current_task_token` (S, never returned by any API), `timer_profile`, `dry_run` (BOOL true), `seeded` (BOOL), `demo_run` (BOOL), `created_at`, `updated_at`.
- `CaseEvents`: PK `case_id` (S), SK `ts_seq` (S, format `<ISO8601 UTC>#<4-digit-seq>`). Attributes: `type`, `message`, `rung`, `meta` (M).

Event `type` values (exact set): `CASE_OPENED`, `JURISDICTION_RESOLVED`, `NOTICE_SENT`, `REMINDER_SENT`, `ESCALATED`, `FIX_CLAIMED`, `CLOSURE_VERIFIED`, `CLOSURE_REJECTED`, `UNRESOLVED_FINAL`.

Case `status` values (exact set): `OPEN`, `AWAITING_FIX`, `FIX_CLAIMED`, `CLOSED_VERIFIED`, `ESCALATED_DM`, `UNRESOLVED_FINAL`.

---

## 8. S3 bucket

One bucket `argus-${AWS::AccountId}-us-east-1`. Block all public access. Lifecycle: expire `uploads/` after 14 days. CORS: GET/PUT/HEAD from `FrontendOrigin` and `http://localhost:5173`, headers `*`, max age 3000. Prefixes: `uploads/` (photos, key format `uploads/<uuid4>.jpg|png`), `tenders/` (PDFs I upload manually), `eval/` (result JSON), `exports/` (scheduled scores).

---

## 9. API (all under `/v1`; implement in `contracts/openapi.yaml` FIRST in Phase 0)

All responses JSON. Timestamps ISO-8601 UTC. IDs: case ids `CS-` + 6 uppercase alphanumerics.

| Method & path | Request | Success response |
|---|---|---|
| `GET /health` | – | `{"status":"ok","time":"..."}` |
| `GET /hotspots` | – | `{"hotspots":[{hotspot_id,name,lat,lng,coord_verified,provenance,features,road:{road_id,name,road_class,width_ft,provenance},jurisdiction,warranty,assets:[asset...]}]}` |
| `GET /risk` | query: `mode=whatif\|live` (default whatif), `rain_3h_mm`, `rain_prev24h_mm`, `traffic_slowdown` (defaults 0; ignored in live mode) | `{"mode","generated_at","inputs":{rain_3h_mm,rain_prev24h_mm,traffic_slowdown,source},"model":{version,fitted},"scores":[RiskScore + hazard_under_water{score,weight,asset_ids}]}` |
| `GET /assets` | – | `{"assets":[...]}` |
| `POST /uploads/presign` | `{"purpose":"report\|fix","content_type":"image/jpeg\|image/png"}` | `{"upload_url","s3_key","expires_in":300}` (presigned PUT, content-type enforced) |
| `POST /analyze` | `{"s3_key"}` | `{"analysis":HazardAnalysis}` |
| `POST /resolve` | `{"lat","lng","asset_type"}` | `{"road","jurisdiction","warranty"}` (used by the report modal before opening a case) |
| `POST /cases` | `{"hotspot_id"?, "lat"?, "lng"?, "asset_type"?, "analysis"?, "photo_key"?, "timer_profile":"demo\|real"}` (either `hotspot_id` or `lat`+`lng`) | `201` Case |
| `GET /cases` | – | `{"cases":[Case summary]}` newest first, max 50 |
| `GET /cases/{case_id}` | – | `{"case":Case,"events":[CaseEvent...],"photo_url"?}` (`photo_url` presigned GET, 1 h) |
| `POST /cases/{case_id}/claim-fix` | `{"s3_key","lat","lng"}` | `{"accepted":bool,"reason":"VERIFIED\|TOO_FAR\|HAZARD_STILL_PRESENT\|LOCATION_MISMATCH\|LOW_CONFIDENCE\|CASE_NOT_OPEN","distance_m":0.0,"verification":{...}}` |
| `POST /tender/clause` | `{"doc_key"}` (must start with `tenders/`) | `{"found","quote","page_hint","verified_in_text":bool\|null}` |
| `GET /eval/results` | – | `{"rdd2022":{...}\|null,"backtest":{...}\|null}` read from S3 `eval/rdd2022.json` and `eval/backtest.json`; null when absent |

Error codes (use exactly): `BAD_REQUEST` 400, `NOT_FOUND` 404, `CONFLICT` 409, `IMAGE_TOO_LARGE` 413, `MODEL_ERROR` 502, `INTERNAL` 500.

`POST /cases` behaviour, in order: (1) validate; (2) resolve the road (from the hotspot's `road_id`, or `road_for_point`); (3) compute jurisdiction and warranty; (4) write the Case (status `OPEN`, rung = jurisdiction.start_rung, `dry_run` true) and events `CASE_OPENED` + `JURISDICTION_RESOLVED`; (5) start the Step Functions execution with the input below; (6) store `execution_arn`; (7) return 201. If starting the execution fails, set status `OPEN`, add an event with `meta.error`, and return 502 `INTERNAL`.

Timer profiles (seconds, for rungs 1–4):
- `demo`: `[20, 20, 20, 20]`
- `real`: `[259200, 172800, 172800, 259200]` (3 d, 2 d, 2 d, 3 d)

`claim-fix` behaviour, in order: (1) load the case; if status is not `AWAITING_FIX`/`OPEN`/`ESCALATED_DM`, return `CASE_NOT_OPEN`; (2) `distance_m = haversine(claim, case location)`; if > 25 → `accepted:false, reason:TOO_FAR` and append `CLOSURE_REJECTED` (no Nova call, no state machine failure; the claimant may retry); (3) download both images (before = `case.photo_key` or the asset's `reference_photo_key`, may be none; after = `s3_key`), call `verify_fix`; (4) accept iff `hazard_still_present == false` AND (`same_location_plausible == true` OR `null`) AND `confidence >= 0.6`; (5) on accept: append `FIX_CLAIMED`, `CLOSURE_VERIFIED`, call `states:SendTaskSuccess` with the stored token and `{"verified":true}`; on reject (hazard present / mismatch / low confidence): append `CLOSURE_REJECTED` and call `states:SendTaskFailure` with error `ClosureRejected` (this triggers escalation). The client-supplied coordinates are labelled in the UI as "location attested by claimant".

---

## 10. Scheduled scoring (`scheduled_score`)

EventBridge rule `rate(1 hour)` invokes `scheduled_score`. It fetches live rainfall for Delhi (28.6139, 77.2090) from Open-Meteo Forecast: `hourly=precipitation&past_hours=24&forecast_hours=3&timezone=UTC`. Compute `rain_prev24h_mm` = sum of the 24 past hours; `rain_3h_mm` = sum of the next 3 hours. Score all hotspots (traffic 0, unless `ENABLE_TOMTOM=true`: for each hotspot GET `https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point=<lat>,<lng>&key=<key>`, `slowdown = clip(1 - currentSpeed/freeFlowSpeed, 0, 1)`; on any failure use 0 and note it). Write the full `/risk`-shaped payload with `"mode":"live"` to `s3://<bucket>/exports/latest_scores.json`. `GET /risk?mode=live` reads that object; if absent or the Open-Meteo call failed, return 503-style `MODEL_ERROR` with message "Live scores not available yet" and the UI falls back to what-if mode. The scheduled Lambda never sends emails and never opens cases.

---

## 11. Photo reporting flow (frontend ↔ API)

1. Client resizes the chosen image so the long edge ≤ 1280 px, re-encodes JPEG quality 0.85 (canvas).
2. `POST /uploads/presign` → `PUT` the blob to `upload_url` with the same `Content-Type`.
3. `POST /analyze` → show the analysis card.
4. User picks a location: (a) the currently selected hotspot (default), (b) "Use my location" (browser geolocation), or (c) click on the map.
5. `POST /resolve` → show the Blame-chain card (13.4).
6. `POST /cases` with the analysis, `photo_key`, and `timer_profile` (default "demo", visible toggle "Demo timers (20 s per level) / Real timers (days)").
7. Navigate to the case timeline panel.

A "Use selected hotspot location" shortcut must exist so the demo can run on a desktop with no geolocation.

---

## 12. Escalation workflow

### 12.1 State machine (`statemachine/escalation.asl.json`, Standard)
Input:
```json
{"case_id":"CS-ABC123","rung":1,"timers":[20,20,20,20]}
```
States (names exact):
1. `NoticeAgent` (Task, `lambda:invoke` on `sfn_notice_agent`; payload `{case_id, rung, kind}` where `kind` = `initial` if rung equals the case's start rung else `escalation`; `ResultPath: "$.notice"`; Retry on `Lambda.ServiceException`/`TooManyRequestsException` ×2).
2. `WaitForFix` (Task, resource `arn:aws:states:::lambda:invoke.waitForTaskToken`, function `sfn_register_token`, payload `{"case_id.$":"$.case_id","rung.$":"$.rung","token.$":"$$.Task.Token"}`, `TimeoutSecondsPath: "$.rung_timeout_s"`, `ResultPath: "$.fix"`; Catch `States.Timeout` → `NextRung`; Catch `ClosureRejected` → `NextRung`).
   Before this state, a `Pass` state `SetTimeout` sets `rung_timeout_s` using `States.ArrayGetItem($.timers, States.MathAdd($.rung, -1))`.
3. `MarkClosed` (Task Lambda `sfn_mark_closed`) → `Succeed`.
4. `NextRung` (Choice): if `$.rung` < 4 → `IncrementRung` (Pass with `"rung.$": "States.MathAdd($.rung, 1)"`) → `SetTimeout`; else → `MarkUnresolved` (Task Lambda `sfn_mark_closed` with `{"outcome":"UNRESOLVED_FINAL"}`) → `Succeed`.
Because Pass states cannot merge arithmetic with existing fields safely, keep all fields and use `Parameters` to rebuild the full object (`case_id`, `rung`, `timers`, `rung_timeout_s`).
Validate with `sam validate` and a local JSON lint; the definition is loaded via `DefinitionUri` with `DefinitionSubstitutions` for Lambda ARNs.

### 12.2 `sfn_register_token`
Stores `current_task_token` on the Case, sets `status` = `ESCALATED_DM` if rung == 4 else `AWAITING_FIX`, sets `rung`, and appends no event (the notice agent already did). Returns immediately (the state machine waits for the callback).

### 12.3 `sfn_mark_closed`
`outcome` `CLOSED_VERIFIED` (default) sets Case status `CLOSED_VERIFIED`; `UNRESOLVED_FINAL` sets status `UNRESOLVED_FINAL` and appends event `UNRESOLVED_FINAL`. Clears `current_task_token`.

### 12.4 `sfn_notice_agent` (Strands, with guaranteed fallback)
Rung → recipient role (exact):
1. the jurisdiction's `officer_role`
2. "Nodal Officer under the Flood Control Order (illustrative)"
3. "Superintending/Chief Engineer of the owning agency (illustrative)"
4. "District Magistrate (illustrative)"
(For ORPHAN cases the start rung is 4 and the recipient is "District Magistrate (illustrative)" with the purpose "convene agencies to assign ownership".)

Behaviour: load the case; build the notice via the Strands agent; send it through SES; append an event (`NOTICE_SENT` for the first notice of the case, `REMINDER_SENT` for rung-2 reminders, `ESCALATED` for rung ≥ 3 or any ORPHAN notice) with `meta` = `{recipient_role, subject, generated_by:"agent"|"template_fallback", ses_message_id}`.

Strands agent spec:
- `from strands import Agent, tool`; `from strands.models import BedrockModel`; `BedrockModel(model_id=NOVA_MODEL_ID, region_name="us-east-1", temperature=0.2)`. Verify current Strands API in docs first (record in VERIFIED_APIS.md).
- Tools (each a `@tool` function returning JSON-serialisable data only): `get_case(case_id)`, `get_blame_chain(case_id)` (returns jurisdiction + warranty + road), `get_event_history(case_id)`, `get_legal_refs()` (from `legal_refs.json`).
- System prompt (exact): "You draft formal, polite, factual complaint notices to Indian civic officials about road hazards. Use ONLY facts returned by the tools. Never invent names, phone numbers, tender numbers, clauses or laws. If warranty status is 'unknown', say the contractor and warranty could not be determined. Keep the body under 180 words. Output ONLY a JSON object with keys \"subject\" and \"body\"."
- Final answer parsed as JSON (strip code fences). If anything fails (import error, timeout, bad JSON, empty body), call `notice_template.build_notice()` instead.
- Hard timeout: 25 s for the agent step, then fallback. Lambda timeout 60 s, memory 1024 MB.

Notice contents (both agent and template MUST include, in this order): DRY-RUN line; case id; location name + `https://www.openstreetmap.org/?mlat=<lat>&mlon=<lng>#map=18/<lat>/<lng>`; hazard type, severity, and whether submerged; a presigned photo link (24 h) if a photo exists; owner agency + officer role + confidence; contractor label + warranty status + end date + days remaining + the quoted clause if `maintenance_clause_text` is non-null; demand: "Please inspect and repair, and reply with a geo-tagged photo of the repaired spot"; deadline = rung timer (`24 hours` text for demo profile is NOT allowed; state "within <n> days" using the real profile values regardless of timer profile); for rung ≥ 2, a line stating prior notices and their dates; the relevant `legal_refs` string(s) for rung 2 and 4. Footer: "Generated by Argus (hackathon prototype)".

SES: `ses.send_email` from `SES_FROM` to `[DRYRUN_INBOX]`, subject `[DRY-RUN] <subject>`; plain-text body only.

---

## 13. Frontend specification

Desktop-first, tuned for 1920×1080 screen recording at 100% zoom. Dark theme: background `#0b1220`, panels `#111a2e`, text `#e6edf7`, accent `#38bdf8`. Risk colours: low `#22c55e`, moderate `#eab308`, high `#f97316`, severe `#ef4444`. Base font size 16 px; panel headings 20 px; numbers on the main panel 28 px so they read in a compressed video.

Env vars (Vite): `VITE_API_BASE` (e.g. `https://xxxx.execute-api.us-east-1.amazonaws.com/v1`), `VITE_LOCATION_API_KEY`, `VITE_AWS_REGION=us-east-1`.

### 13.1 Layout
Full-screen map; left sidebar 360 px (controls + rankings); right panel 420 px (selected hotspot / case / report modal). A top bar with the project name "Argus", a persistent amber **DRY-RUN** pill ("No real notices are sent"), and buttons: "Report a hazard", "Cases", "Model & evidence", "Architecture".

### 13.2 Map
- MapLibre style URL: `https://maps.geo.${region}.amazonaws.com/v2/styles/Standard/descriptor?key=${key}&color-scheme=Dark` (verify with docs, see 0.7). On style load error, fall back to `https://demotiles.maplibre.org/style.json` and show a small amber note "Fallback basemap (Amazon Location unavailable)".
- Initial view: centre `[77.2090, 28.6139]` (lng, lat), zoom 10.6, pitch 0.
- Hotspots: GeoJSON source, circle layer; radius 10 px (14 px when selected); colour from `band`; white 2 px stroke; label layer with hotspot `name` (text-size 12, halo). A pulsing ring (second circle layer, animated radius via `requestAnimationFrame`) on `severe` points only.
- Assets: separate GeoJSON source, small circle (5 px) with black fill and a coloured stroke by type (open_manhole `#f43f5e`, missing_drain_cover `#a855f7`, pothole `#facc15`); visible when the toggle "Show hidden hazards" is ON (default ON) and zoom ≥ 12.
- Hazard-under-water mode toggle ("Hazard under water"): when ON, recolour the hotspot circles by `hazard_under_water.score` using the same bands and show the rank list sorted by that score.
- Rain overlay: a `<canvas>` over the map (pointer-events none) drawing diagonal streaks; streak count = `rain_3h_mm * 3` (cap 300); disabled when rain is 0.
- Click on a hotspot selects it (right panel). Click on empty map does nothing except when "pick location" mode is active in the report modal.

### 13.3 Left sidebar controls
- Mode switch: **What-if** (default) / **Live (hourly)**. If live fails, show an inline notice and revert to What-if.
- Slider 1: "Rain in next 3 h" 0–100 mm step 5; slider 2: "Rain in previous 24 h" 0–100 mm step 5; slider 3: "Traffic slowdown (simulated)" 0–100 % step 5. Preset buttons: Light (10/10/10 %), Heavy (40/30/30 %), Extreme (80/60/60 %), Clear (0/0/0).
- Debounce 200 ms then `GET /risk`; keep the previous scores visible while loading (no flicker); show the text "N of M points above 50 %".
- Ranking list: top 10 by probability (or by hazard-under-water when that mode is on), each row with name, band chip, probability as a percentage, and a click-to-select action.
- Legend and the exact honesty banner text from section 1.

### 13.4 Right panel — selected hotspot
Header: name, provenance chips, `coord_verified` chip ("location unverified" in amber when false). Sections:
1. **Risk drivers**: horizontal bars for the drivers returned by the API (positive contributions to the right in accent colour, negatives to the left in grey); "missing data" chip where `missing: true`.
2. **Hidden hazards nearby**: list of assets within 50 m, each with type, severity, provenance chip; plus "hazard-under-water score".
3. **Blame chain card** (this is the hero element; make it visually prominent): vertical chain of five rows, each with an icon and text — Road (name, class, width) → Owner agency (with confidence bar and the `reasons` list collapsed under "Why?") → Officer role → Contractor (label) → Warranty (badge: green "In warranty — N days left", red "Warranty expired", grey "Unknown"; completion and end dates). If `maintenance_clause_text` exists show it in a quote block with a "Quoted from tender (provenance chip)" caption. If `tender_doc_key` exists show a button "Extract clause with Nova" that calls `POST /tender/clause` and renders the quote with a green "verified in PDF text" or an amber "not found verbatim in PDF" label.
4. Button **"Open case for this hotspot"** (opens the report modal pre-set to this hotspot, photo optional for hotspot-based cases).

### 13.5 Report modal
Steps as in section 11, as a single scrolling modal. The analysis card shows `hazard_type`, severity as 5 dots, `submerged` chip, confidence as a percentage, `description`, and `visible_evidence`. If `hazard_type` is `none` or `unclear`, show a warning "Nova could not confirm a hazard" and still allow opening a case with an explicit "Open case anyway" button.

### 13.6 Cases panel and case view
List from `GET /cases` (poll every 5 s while the panel is open) with status chips and a "SEEDED" chip for seeded cases. The case view polls `GET /cases/{id}` every 2 s and shows:
- A horizontal **rung tracker** with 4 steps (Owner → Nodal officer → Chief engineer → DM); the active rung is highlighted; completed rungs are checked.
- A countdown for the current rung (computed from the last event time + the rung's timer; display "waiting for fix" if unknown).
- The event timeline (newest at the bottom), each event with type icon, message, time, and a "show details" toggle for `meta` (including `generated_by` and the email subject).
- An "Email preview" drawer showing the latest notice subject and body from the event `meta`. The notice agent must put `body` into `meta.body` for this purpose.
- A **"Claim fix"** card with: file input, "Use case location (demo)" button (fills lat/lng from the case), and a submit. After submit show the result `reason` with human text: VERIFIED → "Verified closed", TOO_FAR → "Photo location is more than 25 m from the hazard", HAZARD_STILL_PRESENT → "Nova still sees the hazard — case escalates", LOCATION_MISMATCH → "Photo does not appear to show the same spot", LOW_CONFIDENCE → "Not confident enough to close".
- Label under the claim card: "Location is attested by the claimant."

### 13.7 "Model & evidence" panel
Three tabs:
1. **Model**: shows `model.version` and `fitted` from `/risk`, the formulas in plain text, and the sentence "Coefficients are expert priors and have not been fitted." when `fitted` is false.
2. **Hazard-detection accuracy (RDD2022 India)**: from `/eval/results.rdd2022`: sample size, TP/FP/FN/TN, precision, recall, F1, and the model ID used and the date. If null: "Not yet measured."
3. **Backtest replay**: from `/eval/results.backtest`: a dropdown of events (date, `held_out` chip), the top-20 predicted list with a ✔ on those that appear in the reported list, and metrics `precision@20`, `recall`, `random_baseline_precision`, plus the count of reported locations outside the hotspot list. Show an amber chip "in-sample" when `held_out` is false. If null: "No backtest events loaded."

### 13.8 "Architecture" modal
Static inline SVG (no external images): boxes and arrows for Browser/Amplify → API Gateway → Lambda → {DynamoDB, S3, Bedrock Nova 2 Lite, Step Functions → Strands notice agent → SES}, EventBridge → scheduled scoring → S3, Amazon Location (map tiles). Label the two halves "Predict" and "Enforce". Also write the same content as a Mermaid diagram in `docs/ARCHITECTURE.md`.

### 13.9 Demo mode
`?demo=1` in the URL: hides nothing, but (a) pins the map zoom to 11 on load, (b) preselects the `minto_bridge` hotspot, (c) sets the rain sliders to 0, (d) defaults the timer profile to "demo", (e) shows a thin top strip "DEMO MODE — seeded + simulated data is labelled". Also add keyboard shortcuts, active only in demo mode: `1` Light preset, `2` Heavy, `3` Extreme, `0` Clear, `h` toggle hazard-under-water.

### 13.10 Frontend quality rules
- Strict TypeScript, no `any` except at JSON parse boundaries behind a typed adapter in `src/lib/api.ts`.
- Every network call has a loading state, an error state (message from `error.message`), and a retry button.
- The app must not crash if `/eval/results` returns nulls, if `assets` is empty, or if a hotspot has null features.
- No localStorage/sessionStorage dependence for core flows.
- `vitest` tests for: probability colour banding, the `band→colour` mapping, the debounce helper, and API error parsing.

---

## 14. Evaluation scripts (honest numbers only)

### 14.1 `eval/rdd2022_eval.py`
Expects images and Pascal-VOC XML annotations in `eval/data/rdd2022_india/` (I will supply them; `eval/data/README.md` explains this and the dataset licence/attribution). Behaviour:
- If the folder is missing/empty: print instructions and exit 0 (no results file).
- Otherwise select up to 25 images whose XML contains a `D40` (pothole) object and up to 25 whose XML contains none of `D00/D10/D20/D40`, with a fixed random seed 42. Resize like the frontend (long edge ≤ 1280).
- Call `common.nova.analyze_hazard` (the SAME function production uses). Predicted positive = `hazard_type == "pothole"` with `confidence >= 0.5`. Compute TP/FP/FN/TN, precision, recall, F1 at IMAGE level (state "image-level" in the output).
- Write `eval/results/rdd2022.json` with `{"dataset":"RDD2022 India","level":"image","n_pos":..,"n_neg":..,"tp":..,"fp":..,"fn":..,"tn":..,"precision":..,"recall":..,"f1":..,"model_id":..,"run_at":..}` and copy to `s3://<bucket>/eval/rdd2022.json` when env `BUCKET` is set.

### 14.2 `backtest/run_backtest.py` and `backtest/events.json`
`events.json` schema: `[{"event_id":"","date":"YYYY-MM-DD","description":"","held_out":false,"reported_hotspot_ids":["..."],"reported_other_count":0,"source_urls":["..."],"status":"PLACEHOLDER"}]`. Ship ONE placeholder event with `"status":"PLACEHOLDER"` and an empty `reported_hotspot_ids`; the script SKIPS any event with status `PLACEHOLDER` or empty `source_urls`. I will replace it with 3–5 real events from news.
For each valid event: fetch hourly precipitation from Open-Meteo Archive (`https://archive-api.open-meteo.com/v1/archive`, Delhi centre, `hourly=precipitation`, timezone UTC) for the event date and the previous day; take the maximum 3-hour rolling sum of that date as `rain_3h_mm` and the previous day's total as `rain_prev24h_mm`; score all hotspots with traffic 0; take the top 20 by probability (or all if fewer than 20). Metrics: `precision_at_20 = hits / min(20, N)`, `recall = hits / len(reported_hotspot_ids)` (null if none reported), `random_baseline_precision = len(reported_hotspot_ids) / N`. Write `backtest/results/backtest.json` (+ S3 copy) with the per-event top list, flags and metrics. NEVER pad, smooth, or invent results.

---

## 15. Infrastructure (`template.yaml`)

Parameters: `FrontendOrigin` (default `http://localhost:5173`), `SesFrom`, `DryRunInbox`, `NovaModelId` (default `global.amazon.nova-2-lite-v1:0`), `EnableTomtom` (default `false`), `TomtomApiKey` (NoEcho, default empty).
Globals: Runtime `python3.12`, Architectures `[x86_64]`, Timeout 15, MemorySize 512, Layers `[SharedLayer]`, env vars `TABLE_ASSETS`, `TABLE_CASES`, `TABLE_EVENTS`, `BUCKET`, `STATE_MACHINE_ARN`, `NOVA_MODEL_ID`, `SES_FROM`, `DRYRUN_INBOX`, `USE_MOCKS=false`, `ENABLE_TOMTOM`, `TOMTOM_API_KEY`.
Resources: `SharedLayer` (ContentUri `backend/layer/`, compatible runtime python3.12, `RetentionPolicy: Delete`), `StrandsLayer` (ContentUri `backend/layer_strands/`, attached ONLY to `sfn_notice_agent`), HTTP API with CORS, all functions, three tables, bucket + CORS + lifecycle, state machine (Standard, with CloudWatch logging level ALL to a log group retained 7 days), EventBridge hourly rule, and reserved concurrency 5 for `analyze`, `claim_fix`, `tender_clause`, and `sfn_notice_agent`. API throttling: rate 20, burst 40.
IAM (least privilege, per function): Bedrock `bedrock:InvokeModel` on both `arn:aws:bedrock:us-east-1:${AWS::AccountId}:inference-profile/global.amazon.nova-2-lite-v1:0` AND `arn:aws:bedrock:*::foundation-model/amazon.nova-2-lite-v1:0` (the global profile needs the foundation-model ARN across regions); `ses:SendEmail` limited to the identity ARN of `SesFrom`; S3 and DynamoDB scoped to the stack's own resources; `states:StartExecution` on the state machine for `cases_create`; `states:SendTaskSuccess` and `states:SendTaskFailure` on `*` for `claim_fix` (task tokens carry no ARN); `lambda:InvokeFunction` for the state machine on its four Lambdas.
Outputs: `ApiBase`, `BucketName`, `StateMachineArn`, `TableNames`.
`scripts/build_strands_layer.sh`: build with `pip install --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 --only-binary=:all: --target backend/layer_strands/python strands-agents`; delete `boto3`, `botocore`, `s3transfer`, `jmespath`, all `__pycache__` and `tests` dirs; fail if the folder exceeds 200 MB. If Strands cannot be packaged after two attempts, implement the same four tools and the same system prompt as a direct Bedrock Converse tool-use loop in `sfn_notice_agent` (set an env flag `AGENT_BACKEND=converse`), log the decision in `docs/DECISIONS.md`, and continue.
`scripts/deploy.sh`: `sam build && sam deploy --guided` replacement using `samconfig.toml` (`--profile hackathon --region us-east-1 --capabilities CAPABILITY_IAM --resolve-s3`) taking parameters from the shell env; then print the stack outputs and the exact next commands: `python scripts/seed_demo.py`, `cd frontend && VITE_API_BASE=<ApiBase> VITE_LOCATION_API_KEY=... npm run build && (cd dist && zip -r ../dist.zip .)`.
`scripts/smoke_test.sh <ApiBase>`: curls `/health`, `/hotspots` (assert ≥ 10), `/risk?rain_3h_mm=50` (assert scores length == hotspots length and values in [0,1]), `/assets`, `/eval/results`, and exits non-zero on any failure.

---

## 16. Build phases (do in order; each has a Definition of Done)

**Phase 0 — Scaffolding & contracts.** Create the repo layout, `contracts/openapi.yaml` and schemas, `.gitignore`, `.env.example`, `README.md` skeleton, `CREDITS.md`, `AI_TOOLS.md`, `LICENSE`, `docs/HUMAN_TODO.md` (section 17), and an empty-but-valid `template.yaml` with parameters. DoD: `sam validate --lint` passes; the OpenAPI file lints (use `npx @redocly/cli lint`); the layout matches section 3.

**Phase 1 — Data + model core.** Write all `civic_data/*.json` (section 4), and `common/{geo,risk,jurisdiction,warranty,http}.py` with pytest tests. Tests must prove: probability is monotonic non-decreasing in `rain_3h_mm`, `rain_prev24h_mm` and `traffic_slowdown`; an underpass hotspot has higher susceptibility than the same hotspot without the flag; every rule in 5.3 fires on a crafted input including the disputed and no-road cases; warranty calculation across a month-end boundary (completion 2021-02-28 + 60 months → 2026-02-28; completion 2020-08-31 + 6 months → 2021-02-28); `hazard_under_water` caps at weight 1.0; validation errors raise `ValueError`. Then write `scripts/build_features.py` and run it if the network allows (otherwise leave null and note in `docs/PROGRESS.md`). DoD: `pytest` green.

**Phase 2 — Read API.** Functions `health`, `hotspots`, `risk`, `assets`, `eval_results`, `scheduled_score` and the template resources (API, tables, bucket, layer). DoD: `sam build` succeeds; handlers pass local invocation tests (call `handler()` directly in pytest with a fake event, DynamoDB/S3 faked via `unittest.mock`); `GET /risk` response validates against the schema.

**Phase 3 — Frontend map (parallelisable with Phase 4 once Phase 2 contracts are fixed).** Build 13.1–13.4, 13.8, 13.9 against a local mock of the Phase-2 responses in `frontend/src/mocks/` (used only when `VITE_USE_MOCKS=true`; default false). DoD: `tsc --noEmit`, `vitest`, `vite build` pass; use the browser tool to load `http://localhost:5173/?demo=1` and capture screenshots at Light/Extreme presets proving the colours change; save to `docs/screenshots/`.

**Phase 4 — Vision + blame chain write APIs.** Functions `presign`, `analyze`, `tender_clause`, `/resolve` (put it in the `hotspots` function folder as a second route handler or its own folder `resolve/`; if a new folder is added, update section 3 in `docs/DECISIONS.md`), `common/nova.py`, `common/ddb.py`. Frontend: 13.5 steps for upload/analysis/blame chain. DoD: unit tests with `nova.py` boto3 calls mocked prove: forced-tool parsing, JSON fallback, retry with the fallback model ID, image-too-large rejection.

**Phase 5 — Case workflow.**
 5a. `notice_template.py`, `cases_create`, `cases_get`, `cases_list`, `claim_fix`, `sfn_register_token`, `sfn_mark_closed`, `sfn_notice_agent` using ONLY the template path, the ASL, SES sending, seeded demo cases.
 5b. Then upgrade `sfn_notice_agent` to the Strands agent with the template fallback, plus the layer script.
 Frontend: 13.6.
 DoD: unit tests cover the distance gate (24.9 m accepted path vs 25.1 m rejected), accept/reject decision table for `claim-fix`, notice contents (every required element present; DRY-RUN line first), and ASL validity.

**Phase 6 — Evidence.** `eval/rdd2022_eval.py`, `backtest/run_backtest.py`, frontend 13.7. DoD: both scripts run without error when their input is missing (exit 0 with instructions) and produce valid output files on a tiny fixture in `tests/fixtures/` (3 fake events, mocked Open-Meteo; 4 fake images with mocked Nova).

**Phase 7 — Polish for video.** `docs/VIDEO_SHOTLIST.md`: a numbered list of the exact click path for each of these shots, each mapped to the UI element that shows it: (1) rain slider 0→100 turning points red; (2) click Minto Bridge → drivers + backtest metric; (3) report a photo → Nova analysis; (4) blame-chain card with warranty badge and quoted clause; (5) notice arriving (email preview drawer) and note that real SES delivery goes to the dry-run inbox; (6) Step Functions rung tracker advancing with demo timers; (7) claim-fix → verified; (8) hazard-under-water toggle; (9) architecture modal. Then run the accessibility basics (labels on inputs, focus rings). DoD: every shot is achievable in `?demo=1` mode in under 2:45 total without a page reload.

**Phase 8 — Deploy readiness.** `README.md` complete (what it is, honesty notes, architecture, how to run locally, how to deploy, how AWS is used, data credits, AI tools used, limitations). `CREDITS.md` complete with at least: Open-Meteo (CC BY 4.0 attribution link), OpenStreetMap contributors (ODbL; for the OSM link in notices), Amazon Location Service, MapLibre GL JS (BSD-3), React, Vite, Tailwind, TanStack Query, strands-agents (Apache-2.0), and RDD2022 (if used; attribution as per its licence; verify the licence and write what you found). DoD: `scripts/smoke_test.sh` exists; `docs/HUMAN_TODO.md` is complete; no secrets in the repo (grep for `AKIA`, `key=` patterns, and `.env`).

---

## 17. `docs/HUMAN_TODO.md` (generate this file with exactly these items, as a checklist)

1. Configure AWS CLI profile `hackathon` (`aws configure sso` or `aws configure --profile hackathon`), region `us-east-1`; confirm with `aws sts get-caller-identity --profile hackathon`.
2. Bedrock console (us-east-1): ensure access to Amazon Nova 2 Lite; run `scripts/smoke_test_nova.py` (create this tiny script in Phase 4: sends a 1-line text prompt via Converse and prints the response and the model ID that worked).
3. SES console (us-east-1): create and verify one email identity (use your own inbox). Pass it as both `SesFrom` and `DryRunInbox`.
4. Amazon Location console: create an API key restricted to actions `geo-maps:*` and `geo-places:SearchText`, with referrers `http://localhost:5173/*` and your Amplify domain (add after the first Amplify deploy). Put it in `frontend/.env.local` as `VITE_LOCATION_API_KEY` and in the shell as `LOCATION_API_KEY` for the geocode script.
5. Run `scripts/deploy.sh`; copy `ApiBase` into `frontend/.env.local`.
6. `python scripts/seed_demo.py`.
7. Put one PWD tender PDF (public, downloaded by you) at `s3://<bucket>/tenders/<name>.pdf` and set one contract's `tender_doc_key` to that key (then redeploy). Optional.
8. Place ~50 RDD2022 India images + XML in `eval/data/rdd2022_india/`; run `python eval/rdd2022_eval.py`. Optional but recommended.
9. Replace the placeholder in `backtest/events.json` with 3–5 real rain-day events from news (include source URLs; set `held_out` honestly); run `python backtest/run_backtest.py`.
10. Review `backend/layer/python/civic_data/hotspots_geocoded.json` against the map, copy verified coordinates into `hotspots.json`, set `coord_verified: true` where confirmed, and correct any road attributes, then redeploy.
11. Build the frontend, zip `dist`, and drag it into a new Amplify Hosting manual deployment; add the Amplify domain to the Location API key referrers and to the `FrontendOrigin` parameter (redeploy the backend).
12. Record the video from `?demo=1` following `docs/VIDEO_SHOTLIST.md`; show Amplify URL, Bedrock, Step Functions execution graph, DynamoDB, EventBridge tabs; upload to YouTube; confirm it opens signed-out.

---

## 18. Global acceptance checklist (run at the end; report each line PASS/FAIL with evidence in `docs/PROGRESS.md`)

- [ ] `pytest` passes; `tsc --noEmit`, `vitest`, `vite build` pass; `sam validate --lint` and `sam build` pass.
- [ ] `GET /risk` is monotonic in rain for every hotspot (test over rain 0, 10, 20 … 100).
- [ ] With no secrets set, the frontend builds and shows a clear error state instead of a blank screen.
- [ ] No email address, phone number, or real firm name exists in any committed file (grep).
- [ ] Every email path prepends `[DRY-RUN]`/`DRY-RUN:`.
- [ ] Every record shown in the UI has a provenance chip; seeded cases show a SEEDED chip.
- [ ] `/eval/results` null states render "Not yet measured" / "No backtest events loaded." and never fake numbers.
- [ ] The state machine definition passes `sam validate` and contains the state names in 12.1.
- [ ] README lists every AWS service used and where it appears in the demo.
- [ ] CREDITS.md and AI_TOOLS.md exist and are complete.

---

## 19. Final report (your last message)

Print: (1) what is built vs deferred, as a table with the phases; (2) every deviation from this spec and why; (3) the exact commands I must run next, in order, from `docs/HUMAN_TODO.md`; (4) any assumption you made about AWS API shapes that I should double-check. Do not claim a feature works unless a test or a screenshot proves it.