# Argus Web teammate demo setup

This starts the Argus Web frontend on your computer and connects it to the deployed public API. You do not need access to the AWS project, AWS CLI, AWS credentials, or the backend source runtime.

## Requirements and startup

Use Node.js 20 or newer and npm. From a terminal:

```bash
git clone --branch feat/aws-integration --single-branch https://github.com/argus-zest/argus.git
cd argus/frontend
npm ci
```

Create `frontend/.env.local` with these public, non-secret values (or export the same variables in your shell):

```dotenv
VITE_API_BASE=https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1
VITE_AWS_REGION=ap-southeast-2
VITE_USE_MOCKS=false
VITE_LOCATION_API_KEY=
```

Then start Vite:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Open **http://localhost:5173**. Keep the port and browser hostname exactly as shown: the deployed API and S3 bucket allow the `http://localhost:5173` origin. `VITE_LOCATION_API_KEY` can remain empty; the app uses its OpenStreetMap tile fallback, which requires normal internet access. No map API key is required for the demo.

## Demo

Open **Cases**, select **CS-BNEZAQ**, and show its persisted report and evidence. It can also be retrieved read-only from:

```text
https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1/cases/CS-BNEZAQ
```

The demo API currently allows unauthenticated access. Do not put credentials or private tokens in Vite variables: all `VITE_*` values are visible in the browser bundle. The frontend calls API Gateway directly; Lambda generates short-lived presigned S3 upload URLs. It does not use AWS credentials stored on the developer's computer.

## Troubleshooting

- **CORS error:** use `http://localhost:5173` (not `127.0.0.1`, another port, or a preview server). If the port is occupied, close your own existing Vite server or use the already running one; do not change the port because the API and S3 CORS rules are restricted to 5173.
- **API/network error:** check internet access and that `VITE_API_BASE` is exactly the URL above, including `/v1`. Verify connectivity with `curl -i https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1/health`, then restart Vite after changing `.env.local`.
- **Missing/live data:** ensure `VITE_USE_MOCKS=false` and `VITE_API_BASE` points to API Gateway. The live API must be reachable; mock fixtures are read-only and are not a substitute for the persisted case.
- **AI analysis unavailable:** regional Nova Lite is configured, but AWS project verification has denied invocation. Do not claim an AI result; use the existing persisted case/manual report demonstration. The Bedrock limitation does not prevent viewing `CS-BNEZAQ`.

The frontend does not require a local Python API, AWS CLI, `aws login`, AWS MCP, IAM keys, or a backend process on the original developer's computer. It does require internet access to API Gateway, the evidence bucket via presigned URLs, and OpenStreetMap tiles.
