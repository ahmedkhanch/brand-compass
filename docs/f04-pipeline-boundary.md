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
