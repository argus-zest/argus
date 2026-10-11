# Human Operator Checklist (docs/HUMAN_TODO.md)

Read [DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md) first. Infrastructure changes, deployment, billable inference, and test writes require explicit approval. MCP identity must match the verified hackathon project before MCP provisioning.

Follow these steps in order to complete cloud configuration and live deployment:

- [ ] 1. Configure AWS CLI profile `hackathon` (`aws configure sso` or `aws configure --profile hackathon`), region `ap-southeast-2`; confirm with `aws sts get-caller-identity --profile hackathon`.
- [ ] 2. Bedrock console (ap-southeast-2): ensure access to Amazon Nova Lite; verify regional on-demand availability without invoking. Run `scripts/smoke_test_nova.py` only after separate billable-test approval; never substitute a cross-Region profile.
- [ ] 3. SES console (ap-southeast-2): create and verify one email identity (use your own inbox). Pass it as both `SesFrom` and `DryRunInbox`.
- [ ] 4. Amazon Location console: create an API key restricted to actions `geo-maps:*` and `geo-places:SearchText`, with referrers `http://localhost:5173/*` and your Amplify domain (add after the first Amplify deploy). Put it in `frontend/.env.local` as `VITE_LOCATION_API_KEY` and in the shell as `LOCATION_API_KEY` for the geocode script.
- [ ] 5. Install SAM CLI, run Sydney SAM validation and build, review changes/charges, and obtain deployment approval. Set EXPECTED_AWS_ACCOUNT_ID from verified hackathon STS plus verified SES_FROM/DRYRUN_INBOX, then run `scripts/deploy.sh`. Copy actual ApiBase and VITE_AWS_REGION=ap-southeast-2 into ignored frontend/.env.local.
- [ ] 6. After bounded test-write approval, run `python scripts/seed_demo.py --profile hackathon --region ap-southeast-2`.
- [ ] 7. Put one PWD tender PDF (public, downloaded by you) at `s3://<bucket>/tenders/<name>.pdf` and set one contract's `tender_doc_key` to that key (then redeploy). Optional.
- [ ] 8. Place ~50 RDD2022 India images + XML in `eval/data/rdd2022_india/`; run `python eval/rdd2022_eval.py`. Optional but recommended.
- [ ] 9. Replace the placeholder in `backtest/events.json` with 3–5 real rain-day events from news (include source URLs; set `held_out` honestly); run `python backtest/run_backtest.py`.
- [ ] 10. Review `backend/layer/python/civic_data/hotspots_geocoded.json` against the map, copy verified coordinates into `hotspots.json`, set `coord_verified: true` where confirmed, and correct any road attributes, then redeploy.
- [ ] 11. Build the frontend and upload `dist` to Amplify Hosting; add the Amplify domain to the Location API key referrers. API Gateway and evidence-bucket CORS in `template.yaml` explicitly allow the deployed Amplify origin and localhost:5173.
- [ ] 12. Record the video from `?demo=1` following `docs/VIDEO_SHOTLIST.md`; show Amplify URL, Bedrock, Step Functions execution graph, DynamoDB, EventBridge tabs; upload to YouTube; confirm it opens signed-out.
