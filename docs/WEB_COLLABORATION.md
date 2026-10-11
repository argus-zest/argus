# Argus Web collaboration baseline — 2026-10-11

Use `dev/web-latest` for frontend work. It extends the committed Sydney Region migration with the restored API/type modules, response validation, upload handling repairs, explicitly labeled development fixtures, and frontend tests. The original UI components and animation implementation are preserved. `SPEC.md` and the dependency lockfile are unchanged.

The associated schema generator and contract-boundary tests are included so the restored client remains reproducible. Backend inference changes, deployment safeguards, and deployment-readiness documentation are kept separately on `feat/aws-integration`.

Run `npm ci` in `frontend/`, then `npm test` and `npm run build`. Configure public browser settings using `frontend/.env.example`; keep actual `.env.local` files untracked. Local read-only fixtures require `VITE_USE_MOCKS=true` in the development server. They do not simulate uploads, case persistence, or live inference.

Baseline verification: 12 dependency-free API runtime checks passed with Node 24. Full TypeScript, Vitest, Vite build, and browser verification remain unverified: package installation is blocked by DNS failures and Chromium cannot launch in the execution sandbox. This is the latest intended frontend source baseline, not a fully validated release.

For the animation change, branch from `dev/web-latest`, keep the diff limited to the intended frontend animation, and submit it for review. Integration into `feat/aws-integration` will happen at a later clean checkpoint. Do not deploy infrastructure or change shared backend configuration as part of the animation work.
