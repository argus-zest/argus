# Verified AWS APIs (docs/VERIFIED_APIS.md)

Verification log for external service endpoints and AWS APIs per Section 0.7:

1. **Amazon Bedrock Converse API:**
   - **Service:** `bedrock-runtime`
   - **Primary Model ID:** `global.amazon.nova-2-lite-v1:0` (Global Inference Profile in us-east-1)
   - **Fallback Model ID:** `amazon.nova-2-lite-v1:0`
   - **Endpoint / Operation:** `converse(modelId, messages, system, inferenceConfig, toolConfig)`
   - **Document input format:** Document blocks with `format: "pdf"` and name `[a-zA-Z0-9 -]+`.

2. **Amazon Location Service Maps & Places:**
   - **Style Descriptor:** `https://maps.geo.us-east-1.amazonaws.com/v2/styles/Standard/descriptor?key=${key}&color-scheme=Dark`
   - **Places SearchText:** `geo-places:SearchText` / `https://places.geo.us-east-1.amazonaws.com/places/v0/text`

3. **Open-Meteo APIs:**
   - **Elevation API:** `https://api.open-meteo.com/v1/elevation?latitude=...&longitude=...`
   - **Forecast API:** `https://api.open-meteo.com/v1/forecast?latitude=28.6139&longitude=77.2090&hourly=precipitation&past_hours=24&forecast_hours=3&timezone=UTC`
   - **Archive API:** `https://archive-api.open-meteo.com/v1/archive?latitude=28.6139&longitude=77.2090&hourly=precipitation&timezone=UTC`
