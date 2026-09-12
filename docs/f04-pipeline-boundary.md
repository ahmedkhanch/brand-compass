# F04-A — Boundary for report submission and pipeline persistence

`POST /api/v1/brands/analyze` authenticates the caller and delegates the report
submission to `app.services.report_submission`. That service applies the existing
rate-limit and one-credit policy, then asks repositories to create the owned Brand
and queued Report. The route passes the resulting immutable job data to the queue
adapter; it does not select or mutate ORM models.

Both the local queue adapter and ARQ worker call `app.services.report_pipeline`.
That service owns the `queued -> running -> complete|failed` writes and delegates
all SQLAlchemy work to `app.repositories.report_runs`. It stores the legacy report
payload, scores, and `_costs` records identically for either runner path.

Schema creation is no longer an API-startup side effect. Deployments must run
Alembic before starting API or worker processes. This PR does not change the
credit policy, add a schema revision, or validate a real provider collection.

The API operation remains documented by FastAPI Swagger at `/docs`; this document
describes implementation boundaries and is not a second route catalog.
