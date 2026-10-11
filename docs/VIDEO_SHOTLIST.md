# Video Demonstration Shotlist — Argus

This document defines the exact step-by-step click path to record the complete demonstration video in under **2 minutes and 45 seconds** without a single page reload.

Start URL: `http://localhost:5173/?demo=1` (or deployed AWS Amplify URL with `?demo=1`).

---

## Shot Sequence

### Shot 1: Rain Simulation (0s – 20s)
- **Goal:** Demonstrate continuous risk recalculation and color transition under monsoon rainfall.
- **Action / Click Path:**
  1. Open app at `?demo=1`. Observe initial clear state (all points green / low).
  2. Drag the slider **"Rain in next 3 h"** from `0 mm` up to `100 mm` (or press preset button **[Extreme]** / shortcut key `3`).
  3. Observe Central Map: diagonal rain streak canvas overlay appears; hotspot circle markers shift from green (#22c55e) to orange (#f97316) and severe red (#ef4444) with animated pulsing halo rings on severe locations.
  4. Note in Left Sidebar: Counter shows *"N of M points > 50%"* updating live without flicker.
- **UI Elements:** Sliders panel, Rain Canvas overlay, Hotspot circles layer, Pulsing severe halo.

---

### Shot 2: Hotspot Drill-down & Risk Drivers (20s – 40s)
- **Goal:** Show topographic drivers, relative elevation, and backtest evidence.
- **Action / Click Path:**
  1. In the Left Sidebar rankings list (or directly on the map), click **"Minto Bridge"**.
  2. Map flies smoothly to Minto Bridge at zoom 12.5+.
  3. Right Panel opens displaying:
     - 28px Waterlogging Probability number (e.g. 94%)
     - **Risk Drivers** section with horizontal divergence bars: depression (+2.45), low elevation (+1.80), underpass flag (+1.20).
     - **Hidden Hazards Nearby (< 50m)**: open manhole asset with severity 4/5.
- **UI Elements:** Right Panel Header, Divergence Bar Chart, Nearby Hazards card.

---

### Shot 3: Photo Reporting & Amazon Nova Lite Inspection (40s – 1m 05s)
- **Goal:** Upload a street hazard photo and show automated Bedrock Nova Lite triage.
- **Action / Click Path:**
  1. In the Top Bar, click **"Report a hazard"** (or click **"Open case for this hotspot"** in the Right Panel).
  2. The Report Modal opens.
  3. Under Step 1, click file upload and select sample road hazard image (`pothole.jpg` or `manhole.jpg`).
  4. Observe loading indicator: *"Uploading resized image to S3... Analyzing hazard with Amazon Nova Lite..."*.
  5. The Nova Assessment card renders with:
     - Hazard type: `Pothole`
     - Severity: 4 out of 5 red dots
     - Submerged indicator chip: `NO` / `YES`
     - Confidence: `88%`
     - Verbatim visual evidence text: *"Irregular dark crater in bituminous pavement."*
- **UI Elements:** Report Modal, S3 presigned upload handler, Nova Assessment card.

---

### Shot 4: Accountability Blame Chain & Warranty Badge (1m 05s – 1m 25s)
- **Goal:** Show deterministic attribution to road agency, contractor warranty, and tender clause.
- **Action / Click Path:**
  1. In Report Modal (or Right Panel), scroll down to **"Accountability & Blame Chain"**.
  2. Highlight the 5 vertical steps:
     - **Road:** Minto Road (Class: Arterial, Width: 80 ft)
     - **Agency:** PWD (Confidence: 80% — click "Why?" to show width rule `width_ft >= 60`)
     - **Officer Role:** Executive Engineer, PWD Division (illustrative)
     - **Contractor:** Contractor A (demo)
     - **Warranty Badge:** Green pill *"In warranty — 120 days left"*
  3. If tender doc exists: Click **"Extract clause with Nova"** to display verbatim maintenance clause quote with green *"verified in PDF text"* badge.
- **UI Elements:** Blame Chain Card, Collapsible Why list, Warranty Badge, Tender Clause quote block.

---

### Shot 5: Complaint Notice Dispatch & Email Preview (1m 25s – 1m 45s)
- **Goal:** Open case, trigger Step Functions, and inspect the generated complaint notice.
- **Action / Click Path:**
  1. In Report Modal, select timer profile **"Demo Timers (20s per level)"** and click **"Submit & Open Case"**.
  2. The Modal closes and automatically opens the **Cases Modal** focused on the new case `CS-XXXXXX`.
  3. Click **"View email preview"** drawer.
  4. Inspect the plaintext notice:
     - First line: `DRY-RUN: this notice was NOT sent to any official.`
     - Case ID, coordinates + OpenStreetMap verification URL.
     - Accountable officer role and contractor defect liability clause.
     - State clearly for video: *"All emails route safely to our verified DRYRUN_INBOX via Amazon SES."*
- **UI Elements:** Cases Modal, Email Preview Drawer, SES Dry-run banner.

---

### Shot 6: Step Functions 4-Rung Escalation Tracker (1m 45s – 2m 05s)
- **Goal:** Demonstrate timed automated escalation across administrative tiers.
- **Action / Click Path:**
  1. Look at the horizontal **Escalation Rung Tracker** (Owner → Nodal Officer → Chief Engineer → District Magistrate).
  2. Observe live 20-second countdown timer: *"Auto-escalate in: 18s... 10s... 2s"*.
  3. As the timer expires, the state machine fires: Rung 1 gets a green checkmark, Rung 2 highlights in amber with a pulsing clock icon, and the event log appends `REMINDER_SENT`.
  4. (Optional) Show AWS Console tab of the Step Functions execution graph showing the `WaitForFix` task token.
- **UI Elements:** 4-Step Horizontal Rung Tracker, Live Countdown timer, Event Audit Timeline.

---

### Shot 7: Citizen Claim Fix & AI Verification (2m 05s – 2m 25s)
- **Goal:** Submit a proof-of-fix photo, pass distance constraint, and verify resolution.
- **Action / Click Path:**
  1. Under the **"Claim Fix"** card, select a repaired road image.
  2. Click **"Use case location (demo)"** to populate attested coordinates within 5 meters of hazard.
  3. Click **"Submit Claim & Verify"**.
  4. Nova inspects before & after photos:
     - Result box displays in emerald green: *"Verified closed — road hazard successfully resolved! Explanation: Repaired spot verified clear with smooth asphalt surface."*
     - Status updates immediately to `CLOSED_VERIFIED`.
- **UI Elements:** Claim Fix card, Distance gate indicator, Verification explanation card.

---

### Shot 8: Hazard Under Water Mode (2m 25s – 2m 35s)
- **Goal:** Reveal hidden hazards underneath flooded road segments.
- **Action / Click Path:**
  1. Close Cases Modal to return to Map View.
  2. Toggle **"Hazard under water"** switch in the Left Sidebar (or press keyboard shortcut `h`).
  3. Hotspot markers recolor dynamically based on the co-location of open manholes and missing drain covers.
  4. The sidebar ranking reorders to prioritize spots where severe hidden traps threaten lives under murky water.
- **UI Elements:** Hazard under water toggle, Re-weighted ranking list, Asset marker circles.

---

### Shot 9: System Architecture & Evidence Modals (2m 35s – 2m 45s)
- **Goal:** Prove serverless AWS implementation and honest empirical methodology.
- **Action / Click Path:**
  1. In the Top Bar, click **"Architecture"**:
     - Displays the interactive dual-pipeline SVG architecture diagram dividing **Predict** (EventBridge, Open-Meteo, S3, MapLibre) and **Enforce** (Bedrock Nova Lite, Step Functions, SES, DynamoDB).
  2. Close Architecture modal and click **"Model & evidence"**:
     - Tab 1: plain-text formulas with expert prior note.
     - Tab 2: RDD2022 accuracy metrics.
     - Tab 3: Backtest replay with Precision@20 and verified historical hits.
- **UI Elements:** Architecture Modal SVG, Evidence Modal tabs.

---

## Total Run Time: ~2 minutes 35 seconds (No Page Reloads)
