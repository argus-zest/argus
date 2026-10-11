# Argus Web — deadline demo

The backend is deployed to AWS project 262952461520 in ap-southeast-2. The frontend is local and uses the actual API, not mock responses.

## Open the application

The development server is already serving http://localhost:5173. If it needs restarting:

```bash
cd /home/ansh/Projects/argus-aws/argus/frontend
VITE_API_BASE=https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1 \
VITE_AWS_REGION=ap-southeast-2 VITE_USE_MOCKS=false VITE_LOCATION_API_KEY= \
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Use **http://localhost:5173**, not 127.0.0.1, as the browser origin. A port-in-use error means the existing server may already be running; do not kill unrelated processes.

Read-only API checks:

```bash
cd /home/ansh/Projects/argus-aws/argus
bash scripts/smoke_test.sh https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1
curl -fsS https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1/health
```

## Suggested recording sequence

1. Show the live map and hotspot/corridor/risk views; change a what-if input and explain the calculated risk. Map tiles use the existing OpenStreetMap fallback.
2. Open Cases and select **CS-BNEZAQ**. It is the actual disposable report uploaded and persisted during the approved live test. Its image is the Argus logo, not a real hazard image.
3. Show case detail and evidence, then reload and reopen the same case to demonstrate DynamoDB persistence. Seed-labelled cases are illustrative records.
4. Show notice history: SES accepted a dry-run email only to the verified demo inbox; template fallback generated its text. Do not claim mailbox delivery unless personally checked.
5. State the AI limitation plainly: regional Nova Lite is configured, but AWS project verification currently denies inference. The submitted report used the existing manual path; no AI result was fabricated.

Do not claim the entire escalation or verified closure passed: the first execution exposed a timeout-context bug. Its correction is deployed and verified in the active workflow definition; the failed execution remains recorded. Do not create additional automated reports, restart failed executions or send more test messages merely for recording. Preserve existing feature views; no functionality was removed for deployment.

No AWS-hosted frontend URL, mobile integration or physical-device installation was tested. Public demo API exposure, ongoing hourly scoring/storage/log charges, and production hardening limitations are documented in INTEGRATION_HANDOFF.md. Resource cleanup requires separate approval; do not delete retained evidence.
