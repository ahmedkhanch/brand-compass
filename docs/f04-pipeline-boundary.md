# F04-A — HTTP boundary for report submission and pipeline persistence

`POST /api/v1/brands/analyze` authenticates the caller and delegates the report
submission to `app.services.report_submission`. That service applies the existing
rate-limit and one-credit policy, then asks repositories to create the owned Brand
and queued Report. Before a credit is taken, the service requires the per-instance
job signing secret and internal API origin. It signs the owner, report ID, exact
brand input, audience, purpose and expiry into a short-lived job token. The public
response never exposes that token.

Both the local queue adapter and ARQ worker call
`POST /api/v1/internal/report-jobs/{report_id}/execute` through the shared HTTP
adapter. They contain no database session or pipeline import. The endpoint verifies
the server token before it passes the signed claims to `app.services.report_pipeline`.
That service owns `queued -> running -> complete|failed` writes and delegates all
SQLAlchemy work to `app.repositories.report_runs`.

The repository claims only `queued` reports with a conditional SQLAlchemy update;
a replay or concurrent duplicate returns a conflict before the diagnostic runs.
Engine and completion persistence failures roll back and attempt to persist the
safe terminal message `Analysis execution failed`. This PR does not add a schema
revision, change the credit policy, or validate real provider collection.

The API operation remains documented by FastAPI Swagger at `/docs`; this document
describes implementation boundaries and is not a second route catalog.

## Configuration and failure behavior

Set `REPORT_JOB_SECRET` to a generated secret of at least 32 bytes and
`INTERNAL_API_ORIGIN` to the API's HTTP(S) origin, without credentials, path,
query or fragment. Keep both settings in the server's secret/configuration
store. Tokens live for `REPORT_JOB_TOKEN_TTL_SECONDS` (default 300; supported
range 30–3600 seconds). Both API and ARQ instances use the same signing key.
The local fallback dispatches immediately after the submission commits.

`INTERNAL_API_TIMEOUT_SECONDS` defaults to 330 seconds, allowing the existing
300-second worker execution budget plus transport overhead. A queue backlog may
still outlive a token; automatic retry, renewal, refunds and recovery of an
interrupted `running` report are not implemented in this delivery.

Empty names are rejected by the public request schema before charging. Signing
must succeed before the debit and queued report commit. If terminal persistence
fails, the execution API returns a sanitized 503, rather than claiming a final
status that was not written. Operators must inspect/reconcile such running jobs;
a replay cannot bypass the atomic claim.

## Reproducible validation

Install Python validation dependencies from `backend/requirements-ci.txt` in an
isolated environment and run `npm ci --prefix frontend`, then
`npm exec --prefix frontend -- playwright install --with-deps chromium`.
The dependency snapshot
includes greenlet because SQLAlchemy's async engine needs it on every platform.
The coverage configuration explicitly tracks greenlets.

Run `python ops/validate.py --base <upstream-develop-sha> --reports <artifact-dir>`.
It executes all baseline and candidate backend tests, frontend lint and webpack
builds, compares test identities/failure signatures, requires every new test to
pass, enforces 100% changed Python line coverage, and runs the validation page's
SSR coverage test. It then starts isolated API/frontend servers and verifies
Swagger, anonymous execution rejection, and desktop/mobile browser behavior.
Temporary baseline worktrees and smoke server processes are cleaned on exit.
The server workflow uses this same command and uploads native logs/reports.

The inherited Ads-fixture assertion and frontend lint errors remain visible in
both runs; comparison accepts only unchanged failures, not additional failures
or missing previously passing tests. The report labels this as no regression,
not an entirely green legacy suite. Native HTTP evidence, browser screenshots
and a Playwright trace are included in the CI artifacts. Swagger `/docs` remains the API catalog;
`/tests#pipeline-boundary` remains the sole functional validation section.
