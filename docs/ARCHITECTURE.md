# Architecture & System Design — Argus

Argus implements an automated dual-pipeline architecture:
1. **Predict:** Risk assessment & hydrological susceptibility modeling for Delhi arterial roads.
2. **Enforce:** AI hazard inspection, deterministic blame chain attribution, and 4-rung Step Functions escalation.

---

## 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Client Tier"]
        Browser["React 18 + Vite Web App\n(AWS Amplify Hosting)"]
        MapLibre["MapLibre GL JS\nDark Basemap"]
        LocService["Amazon Location Service\nStandard Dark Style Tiles"]
    end

    subgraph Ingestion["API Gateway & Ingestion"]
        ApiGw["Amazon API Gateway HTTP API v2\n(/v1/*)"]
    end

    subgraph Predict["Predict Pipeline"]
        EventBridge["Amazon EventBridge\nHourly Rate Rule"]
        ScheduledScore["scheduled_score Lambda\n(Hourly Delhi Forecast)"]
        RiskLambda["risk Lambda\n(What-if & Live Scoring)"]
        HotspotsLambda["hotspots Lambda\n(Geo Contours & Features)"]
        OpenMeteo["Open-Meteo API\n(Elevation & Rain Archive)"]
    end

    subgraph Enforce["Enforce Pipeline"]
        PresignLambda["presign Lambda\n(S3 PUT Presigned URLs)"]
        AnalyzeLambda["analyze Lambda\n(Nova 2 Lite Inspection)"]
        CasesLambda["cases Lambda\n(CRUD & Escalation Init)"]
        ClaimFixLambda["claim_fix Lambda\n(TaskToken & Verification)"]
        Nova["Amazon Bedrock\n(Amazon Nova 2 Lite)"]
        StepFunctions["AWS Step Functions\n4-Rung Escalation State Machine"]
        NoticeAgent["Strands Notice Agent Lambda\n(Bedrock Converse + Fallback)"]
        Ses["Amazon SES\n[DRY-RUN] Notice Delivery"]
    end

    subgraph Storage["Storage Tier"]
        S3Bucket["Amazon S3 Bucket\n(uploads/, exports/, eval/)"]
        DdbCases[("DynamoDB Cases")]
        DdbEvents[("DynamoDB CaseEvents")]
        DdbAssets[("DynamoDB Assets")]
    end

    %% Client flows
    Browser --> MapLibre
    MapLibre -.->|Vector Tiles| LocService
    Browser -->|HTTPS REST| ApiGw

    %% Predict flows
    EventBridge -->|hourly| ScheduledScore
    ScheduledScore -->|rain inputs| OpenMeteo
    ScheduledScore -->|export latest_scores.json| S3Bucket
    ApiGw -->|GET /risk| RiskLambda
    ApiGw -->|GET /hotspots| HotspotsLambda
    RiskLambda -->|read live cache| S3Bucket

    %% Enforce flows
    ApiGw -->|POST /uploads/presign| PresignLambda
    PresignLambda -->|Presigned URL| Browser
    Browser -->|Direct Image Upload| S3Bucket
    ApiGw -->|POST /analyze| AnalyzeLambda
    AnalyzeLambda -->|Converse with Vision| Nova
    ApiGw -->|POST /cases| CasesLambda
    CasesLambda -->|Record Case| DdbCases
    CasesLambda -->|Record Event| DdbEvents
    CasesLambda -->|Start Execution| StepFunctions
    StepFunctions -->|Invoke Rung Action| NoticeAgent
    NoticeAgent -->|Draft Notice| Nova
    NoticeAgent -->|Send Plaintext Email| Ses
    ApiGw -->|POST /cases/:id/claim-fix| ClaimFixLambda
    ClaimFixLambda -->|Verify Resolution| Nova
    ClaimFixLambda -->|SendTaskSuccess/Failure| StepFunctions
    StepFunctions -->|Audit History| DdbEvents
    CasesLambda -->|Query / Update| DdbCases
    HotspotsLambda -->|Query Assets| DdbAssets
```

---

## 2. Key Subsystems

### 2.1 Predict Pipeline
- **Susceptibility Scoring:** Computes local topographic depression, relative elevation, underpass indicator, and historic rainfall susceptibility using calibrated logistic transforms.
- **Hourly Live Batch:** `scheduled_score` runs via EventBridge every hour, pulls Delhi rainfall from Open-Meteo, evaluates all hotspots, and stores `latest_scores.json` in S3.
- **Real-Time Simulation:** In What-if mode, the browser dynamically computes response matrices with immediate debounce feedback.

### 2.2 Enforce Pipeline
- **Image Triage & Hazard Extraction:** Photos uploaded directly to S3 via presigned PUTs are analyzed by Amazon Nova 2 Lite using forced tool-calling schemas.
- **Blame Chain & Warranty Tracking:** Deterministically resolves road ownership across NHAI, NDMC, PWD, DJB, and MCD based on road width, highway status, and asset type. Matches maintenance contracts to determine active defect-liability windows.
- **4-Rung Escalation Flow:** An AWS Step Functions state machine governs notice progression:
  1. Rung 1: Executive Engineer / Project Director
  2. Rung 2: Nodal Officer / Superintending Engineer (with prior notice reference)
  3. Rung 3: Chief Engineer
  4. Rung 4: District Magistrate (Convene inter-agency task force for disputed/orphan roads)
- **Closure Verification:** Fixes claimed with new photos are checked against distance constraints (< 25m) and visually inspected by Nova 2 Lite to confirm hazard removal before task tokens are resolved.
