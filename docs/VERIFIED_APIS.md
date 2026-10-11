# Verified AWS APIs (docs/VERIFIED_APIS.md)

Verification log for external service endpoints and AWS APIs per Section 0.7:

1. **Amazon Bedrock Converse API:**
   - **Service:** `bedrock-runtime`
   - **Model ID:** `amazon.nova-lite-v1:0` (In-Region inference in `ap-southeast-2`; no cross-Region profile)
   - **Model capability / availability:** Nova Lite supports image input, Converse, and client-side tool calling; AWS lists In-Region availability in Sydney. See [Nova Lite model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-lite.html#regional-availability).
   - **Fallback:** None. The runtime rejects model ID overrides that could use a cross-Region inference profile.
   - **Endpoint / Operation:** `converse(modelId, messages, system, inferenceConfig, toolConfig)`
   - **Document input format:** Document blocks with `format: "pdf"` and name `[a-zA-Z0-9 -]+`.

2. **Amazon Location Service Maps & Places:**
   - **Style Descriptor:** `https://maps.geo.ap-southeast-2.amazonaws.com/v2/styles/Standard/descriptor?key=${key}&color-scheme=Dark`
   - **Places SearchText:** `geo-places:SearchText` / `https://places.geo.ap-southeast-2.amazonaws.com/places/v0/text`

3. **Open-Meteo APIs:**
   - **Elevation API:** `https://api.open-meteo.com/v1/elevation?latitude=...&longitude=...`
   - **Forecast API:** `https://api.open-meteo.com/v1/forecast?latitude=28.6139&longitude=77.2090&hourly=precipitation&past_hours=24&forecast_hours=3&timezone=UTC`
   - **Archive API:** `https://archive-api.open-meteo.com/v1/archive?latitude=28.6139&longitude=77.2090&hourly=precipitation&timezone=UTC`
