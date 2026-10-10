# Human Operator Checklist (docs/HUMAN_TODO.md)

Follow these steps in order to complete cloud configuration and live deployment:

- [ ] 1. Configure AWS CLI profile `hackathon` (`aws configure sso` or `aws configure --profile hackathon`), region `us-east-1`; confirm with `aws sts get-caller-identity --profile hackathon`.
- [ ] 2. Bedrock console (us-east-1): ensure access to Amazon Nova 2 Lite; run `scripts/smoke_test_nova.py` (sends a 1-line text prompt via Converse and prints the response and the model ID that worked).
- [ ] 3. SES console (us-east-1): create and verify one email identity (use your own inbox). Pass it as both `SesFrom` and `DryRunInbox`.
- [ ] 4. Amazon Location console: create an API key restricted to actions `geo-maps:*` and `geo-places:SearchText`, with referrers `http://localhost:5173/*` and your Amplify domain (add after the first Amplify deploy). Put it in `frontend/.env.local` as `VITE_LOCATION_API_KEY` and in the shell as `LOCATION_API_KEY` for the geocode script.
- [ ] 5. Run `scripts/deploy.sh`; copy `ApiBase` into `frontend/.env.local`.
- [ ] 6. Run `python scripts/seed_demo.py`.
- [ ] 7. Put one PWD tender PDF (public, downloaded by you) at `s3://<bucket>/tenders/<name>.pdf` and set one contract's `tender_doc_key` to that key (then redeploy). Optional.
- [ ] 8. Place ~50 RDD2022 India images + XML in `eval/data/rdd2022_india/`; run `python eval/rdd2022_eval.py`. Optional but recommended.
- [ ] 9. Replace the placeholder in `backtest/events.json` with 3–5 real rain-day events from news (include source URLs; set `held_out` honestly); run `python backtest/run_backtest.py`.
- [ ] 10. Review `backend/layer/python/civic_data/hotspots_geocoded.json` against the map, copy verified coordinates into `hotspots.json`, set `coord_verified: true` where confirmed, and correct any road attributes, then redeploy.
- [ ] 11. Build the frontend, zip `dist`, and drag it into a new Amplify Hosting manual deployment; add the Amplify domain to the Location API key referrers and to the `FrontendOrigin` parameter (redeploy the backend).
- [ ] 12. Record the video from `?demo=1` following `docs/VIDEO_SHOTLIST.md`; show Amplify URL, Bedrock, Step Functions execution graph, DynamoDB, EventBridge tabs; upload to YouTube; confirm it opens signed-out.
