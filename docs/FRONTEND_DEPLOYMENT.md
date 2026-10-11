# Argus Web frontend deployment

## Current status

- Hosting: AWS Amplify Hosting app `argus-web-hackathon`, Region `ap-southeast-2`; manual `demo` branch deployment succeeded on 2026-10-11.
- Global delivery: Amplify uses CloudFront. Project `AGENTS.md`/`CLAUDE.md` explicitly allows CloudFront as a global service; all regional resources remain in `ap-southeast-2`.
- Public URL: <https://demo.d1ygq6l84twsei.amplifyapp.com> (HTTPS returns HTTP 200; static app shell and assets load).
- Source: `feat/aws-integration`, commit `d98fb97bff03e2e013ed6615a82a8abce6a8c6fb`.
- Hosting approach: manual static artifact deployment. This avoids requiring an Amplify GitHub App installation or additional GitHub organization permissions.
- Current integration status: live API reads from Amplify are working after the approved CORS update on 2026-10-11. CloudFormation stack `argus` reached `UPDATE_COMPLETE`.

## Build and public configuration

The production build passed with Node-compatible npm dependencies and the following public Vite variables:

```dotenv
VITE_API_BASE=https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1
VITE_AWS_REGION=ap-southeast-2
VITE_USE_MOCKS=false
VITE_LOCATION_API_KEY=
```

Build commands:

```bash
cd frontend
npm ci
VITE_API_BASE=https://ungyntrr31.execute-api.ap-southeast-2.amazonaws.com/v1 VITE_AWS_REGION=ap-southeast-2 VITE_USE_MOCKS=false VITE_LOCATION_API_KEY= npm run build
```

Upload the contents of `frontend/dist` to Amplify Hosting. No Vite value contains an AWS credential. The frontend calls API Gateway; the backend issues presigned S3 upload URLs. An empty Location key uses the OpenStreetMap fallback.

## SPA fallback

Configure this Amplify 200 rewrite so client-side navigation loads the Vite app while asset requests remain asset requests:

```json
{ "source": "</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|mjs|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>", "target": "/index.html", "status": "200", "condition": null }
```

## Backend CORS update

The required origins are `http://localhost:5173` and `https://demo.d1ygq6l84twsei.amplifyapp.com`. The existing methods and headers remain unchanged: API Gateway allows GET/POST/OPTIONS and all headers; S3 allows GET/PUT/HEAD and all headers.

The previous change set `argus-amplify-cors-20261011` failed while updating `HttpApi` with `Duplicated values are not allowed in allow-origins`. The processed SAM template had already materialized the first `FrontendOrigin` reference as its default literal (`http://localhost:5173`), while the second list member remained a CloudFormation condition that adds localhost when the deployment parameter differs from localhost. Setting the parameter to the Amplify host therefore produced two localhost values. The failed resource event confirms the exact request list was `[http://localhost:5173, http://localhost:5173]`. SAM writes HTTP API CORS into the generated OpenAPI definition, which is why the processed template is the relevant value to inspect ([SAM HTTP API CORS docs](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-httpapi-httpapicorsconfiguration.html)). The stack rolled back to `UPDATE_ROLLBACK_COMPLETE`, and live read-back confirmed both API Gateway and the evidence bucket were restored to localhost only.

The corrected SAM template removes `FrontendOrigin` and its condition, and declares both exact origins once in API and S3 CORS. This avoids the failed parameter/conditional resolution path. The approved change set `samcli-deploy1791729042` executed on 2026-10-11 and reached `UPDATE_COMPLETE`. Read-back confirms API Gateway `AllowOrigins` and S3 `AllowedOrigins` are exactly `[http://localhost:5173, https://demo.d1ygq6l84twsei.amplifyapp.com]`, with no duplicates or trailing slashes. API methods remain GET/POST/OPTIONS; S3 methods remain GET/PUT/HEAD.

The change set contained 25 `Modify` actions and no `Add`/`Remove`: direct CORS changes to `HttpApi.Body` and `StorageBucket.CorsConfiguration`, plus 23 dependent updates (10 IAM roles, 9 Lambda functions, the state machine, EventBridge rule, Lambda permission, and bucket policy). All replacements were `False` except the EventBridge-to-Lambda permission, marked `Conditional` because its `SourceArn` references the rule ARN. The IAM role changes were dynamic reference updates through `StorageBucket.Arn`; the SAM source's policy documents were unchanged. No DynamoDB tables were in the change set; the retained S3 bucket updated in place.

## Verification and limitations

Chromium verified the public HTTPS page loads with no `Backend Connection Required` message, no mock-data banner, no console errors, and no failed network requests. Live `/hotspots`, `/assets`, `/risk`, case list, and `/cases/CS-BNEZAQ` requests returned HTTP 200; the UI rendered ten hotspot/corridor rankings and the `CS-BNEZAQ` case detail. Chromium also verified the existing `http://localhost:5173` frontend returns HTTP 200 and reaches live `/hotspots`, `/assets`, and `/risk` endpoints without browser errors. API OPTIONS preflight succeeded from both Amplify and localhost. The API returned a presigned report-upload URL (not logged or exposed); an OPTIONS preflight against that actual URL returned HTTP 200 for Amplify with PUT and `content-type` allowed. No object was uploaded. The three DynamoDB tables and evidence bucket retained their original physical names and are present after the update.

Regional Nova Lite inference remains blocked by AWS project verification; do not claim successful AI analysis. Full Step Functions escalation remains unverified. The manual report and case retrieval demo remain usable.

## Cost

Pricing is usage-based. Current AWS pricing lists standard build time at $0.01/minute, stored CDN data at $0.023/GB-month, and data transfer at $0.15/GB. The proposed manual deployment builds locally, so it avoids Amplify build-minute charges; storage and transfer can still incur charges. AWS lists allowances for eligible Free Tier customers, but eligibility and remaining credits were not verified. No WAF, custom domain, or additional hosting infrastructure is planned. Consult [Amplify pricing](https://aws.amazon.com/amplify/pricing/) for current rates.
