# Credits & Third-Party Attributions

Argus builds upon and integrates several open-source libraries, open datasets, and cloud services. We gratefully acknowledge their authors and maintainers.

---

### APIs and Datasets

1. **Open-Meteo Weather APIs**
   - **Service:** Weather Forecast API, Historical Archive API, and Elevation API.
   - **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
   - **Attribution:** Weather data by [Open-Meteo.com](https://open-meteo.com/) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

2. **OpenStreetMap**
   - **Service:** Geographic references, coordinates, and map location URLs included in generated hazard notices.
   - **License:** Open Database License (ODbL) 1.0.
   - **Attribution:** Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) available under the Open Database License.

3. **Road Damage Dataset 2022 (RDD2022) India Subset**
   - **Dataset:** Crowdsourced road damage images and Pascal-VOC XML annotations.
   - **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
   - **Attribution:** Maeda, H., Sekimoto, Y., Seto, T., Kashiyama, T., & Omata, H. (2018/2022). Road Damage Detection and Classification.

4. **TomTom Traffic APIs (Optional integration)**
   - **Service:** TomTom Flow Segment Data API.
   - **Terms:** Used under TomTom Developer Terms and Conditions when enabled.

---

### Cloud Services

1. **Amazon Web Services (AWS)**
   - **Amazon Bedrock:** Foundation model inference using Amazon Nova Lite (`amazon.nova-lite-v1:0`).
   - **Amazon Location Service:** Map style descriptors, tiles, and places geocoding.
   - **AWS Step Functions:** Standard workflow state machine orchestration.
   - **Amazon EventBridge:** Scheduled hourly risk scoring rule.
   - **Amazon Simple Email Service (SES):** Dry-run civic escalation notice delivery.
   - **Amazon DynamoDB & Amazon S3:** Serverless datastore and object storage.
   - **AWS Lambda & Amazon API Gateway:** Serverless execution and HTTP API v2.

---

### Open Source Libraries & Frameworks

1. **MapLibre GL JS**
   - **License:** BSD 3-Clause License.
   - **Copyright:** (c) 2020 MapLibre contributors.

2. **React & React DOM**
   - **License:** MIT License.
   - **Copyright:** (c) Meta Platforms, Inc. and affiliates.

3. **Vite**
   - **License:** MIT License.
   - **Copyright:** (c) 2019-present Evan You & Vite Contributors.

4. **Tailwind CSS**
   - **License:** MIT License.
   - **Copyright:** (c) Tailwind Labs, Inc.

5. **@tanstack/react-query**
   - **License:** MIT License.
   - **Copyright:** (c) TanStack.

6. **strands-agents**
   - **License:** Apache License 2.0.
   - **Copyright:** (c) Amazon Web Services.

7. **Boto3 & Botocore**
   - **License:** Apache License 2.0.
   - **Copyright:** (c) Amazon Web Services.

8. **Pytest**
   - **License:** MIT License.
   - **Copyright:** (c) Holger Krekel and pytest-dev team.
