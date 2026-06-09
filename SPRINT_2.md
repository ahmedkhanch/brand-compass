
# Sprint 2 — Production-Grade Backend: Auth, Payments, Database

> **Start:** 2026-06-09
> **Sprint 1 Status:** ✅ Complete
> **Goal:** Transform the local dev prototype into a production-ready SaaS backend

---

## What Sprint 1 Delivered (Recap)

The local dev app can analyze any brand end-to-end: Firecrawl scrape → DeepSeek positioning/SWOT/competitive/recommendations → SerpAPI SEO score → DeepSeek GEO score → full report stored in SQLite. Background processing works via threading. All API routes exist with stubs for Stripe, email, and auth.

## What Sprint 2 Adds

| # | Deliverable | Status |
|---|------------|--------|
| 1 | **Clerk Auth** — real JWT verification, register/login, multi-user isolation | ⬜ |
| 2 | **Stripe Integration** — real checkout sessions, customer portal, webhooks that update subscriptions | ⬜ |
| 3 | **PostgreSQL Migration** — Alembic migrations, asyncpg, Railway-ready | ⬜ |
| 4 | **Cost Tracking** — populate `report_costs` during pipeline runs per provider | ⬜ |
| 5 | **Prompt YAML Extraction** — switch scorers from hardcoded strings to `prompts/templates/*.yml` | ⬜ |
| 6 | **ARQ Worker** — Redis-backed task queue replacing `threading.Thread` | ⬜ |

---

## 1. Clerk Auth — Real User Authentication

### Current State
Dev mode: any bearer token `dev-user-*` creates a unique user. No real auth.

### Target State
- `CLERK_SECRET_KEY` in `.env` → JWT verification activates
- Real Clerk JWTs from the frontend → validated against Clerk's JWKS endpoint
- `GET /api/v1/auth/me` → returns current user profile + tier
- `POST /api/v1/auth/register` → creates user in our DB on first Clerk login
- Multi-user isolation: every query scoped to `user_id`
- Tier gating enforced per real subscription

### Files to Change
- `backend/app/core/deps.py` — already has Clerk JWT logic, just needs testing
- `backend/app/core/clerk.py` — Clerk SDK wrapper
- `backend/.env` — add real Clerk keys

### Acceptance Criteria
- [ ] `dev-user-*` tokens work when `CLERK_SECRET_KEY` is unset (dev mode)
- [ ] Real Clerk JWT rejected with 401 when `CLERK_SECRET_KEY` is set but token invalid
- [ ] Valid Clerk JWT accepted, user auto-created in our DB
- [ ] `GET /auth/me` returns `{ user_id, tier, credits_remaining }`

---

## 2. Stripe Integration — Real Payments

### Current State
Three endpoints return mock URLs. Webhook acknowledges without acting.

### Target State

#### `POST /api/v1/checkout`
- Creates a real Stripe Checkout Session with the correct price ID per tier
- Returns the actual Stripe-hosted payment URL
- Price IDs from `.env`:
  - `STRIPE_PRICE_BOUSSOLE=price_xxx`
  - `STRIPE_PRICE_RADAR=price_xxx`
  - `STRIPE_PRICE_STRATEGE=price_xxx`

#### `POST /api/v1/checkout/portal`
- Creates a real Stripe Customer Portal session
- User can update payment method, cancel, view invoices

#### `POST /api/v1/webhooks/stripe`
- Verifies Stripe webhook signature
- Handles events:
  - `checkout.session.completed` → create/upgrade subscription + reset credits
  - `invoice.paid` → reset monthly credit balance
  - `customer.subscription.deleted` → downgrade to Boussole tier
  - `customer.subscription.updated` → sync tier changes

### Files to Change
- `backend/app/services/stripe.py` — real Stripe SDK calls
- `backend/app/api/v1/subscriptions.py` — wire up checkout/portal
- `backend/app/api/v1/webhooks.py` — real webhook handler
- `backend/.env` — add Stripe keys + price IDs

### Acceptance Criteria
- [ ] Checkout returns real Stripe URL
- [ ] Webhook upgrades subscription on `checkout.completed`
- [ ] Webhook resets credits on `invoice.paid`
- [ ] Webhook downgrades tier on `subscription.deleted`

---

## 3. PostgreSQL Migration

### Current State
SQLite via aiosqlite. Single file, no concurrency.

### Target State
- PostgreSQL via asyncpg for production
- SQLite kept for local dev (auto-detect based on `DATABASE_URL`)
- Alembic migrations for schema versioning
- All existing models compatible with both databases
- Enum types work on both (SQLite uses VARCHAR, PostgreSQL uses native ENUM)

### Files to Change
- `backend/app/config.py` — add `DATABASE_URL` with PostgreSQL default
- `backend/app/database.py` — conditional engine creation
- `backend/migrations/` — initial Alembic migration
- `backend/alembic.ini` — Alembic config
- `backend/app/models/*.py` — ensure PostgreSQL compatibility

### Acceptance Criteria
- [ ] `DATABASE_URL=sqlite+aiosqlite:///...` → SQLite (current behavior)
- [ ] `DATABASE_URL=postgresql+asyncpg://...` → PostgreSQL
- [ ] `alembic upgrade head` creates all tables on PostgreSQL
- [ ] All existing endpoints work on both databases

---

## 4. Cost Tracking

### Current State
`report_costs` table exists but is never written to.

### Target State
- After each provider call during `run_full_diagnostic()`, record:
  - Provider name (deepseek, firecrawl, serpapi)
  - Tokens in/out (for LLM calls)
  - Cost in cents
  - Duration in milliseconds
- Costs calculated from provider pricing:
  - DeepSeek: $0.14/M input, $0.28/M output
  - Firecrawl: $0.0015 per scrape
  - SerpAPI: included in plan

### Files to Change
- `backend/engine/orchestrator.py` — wrap provider calls with cost tracking
- `backend/engine/providers/*.py` — return token counts from API responses

### Acceptance Criteria
- [ ] Each report has 4-8 `report_costs` rows (one per provider call)
- [ ] Total cost per report visible in admin/query
- [ ] Zero-cost runs recorded (providers that don't charge per call)

---

## 5. Prompt YAML Extraction

### Current State
YAML templates exist in `app/prompts/templates/` but scorers use hardcoded Python strings.

### Target State
- `positioning.py` loads from `positioning.yml` instead of inline strings
- `seo.py` uses template variables
- `geo.py` loads from `geo_check.yml`
- Prompt changes don't require code changes — edit YAML, restart server

### Files to Change
- `backend/engine/scorers/positioning.py` — use `load_prompt()`
- `backend/engine/scorers/geo.py` — use `load_prompt()`
- `backend/app/prompts/templates/*.yml` — verify templates match current prompts

### Acceptance Criteria
- [ ] Pipeline produces identical output with YAML templates vs hardcoded prompts
- [ ] Changing a prompt in `.yml` takes effect on next request
- [ ] All 5 templates load without errors

---

## 6. ARQ Worker (Redis Task Queue)

### Current State
Background processing uses `threading.Thread` with dedicated event loops. Works for local dev but doesn't scale.

### Target State
- `redis>=5.0` running locally or in Docker
- ARQ worker picks up report jobs from Redis queue
- `POST /brands/analyze` enqueues job to Redis instead of spawning thread
- Worker runs in separate process: `arq backend.arq_worker.py`
- Fallback: if `REDIS_URL` is unset, use current threading approach (dev mode)
- Brand cache: 24h Redis TTL per README §10

### Files to Change
- `backend/app/api/v1/brands.py` — conditionally enqueue to ARQ vs thread
- `backend/app/jobs/report_worker.py` — already ARQ-compatible
- `backend/arq_worker.py` — already configured
- `backend/app/config.py` — add `REDIS_URL` default for local dev

### Acceptance Criteria
- [ ] `REDIS_URL` unset → uses threading (current behavior, unchanged)
- [ ] `REDIS_URL=redis://localhost:6379` → enqueues to Redis, ARQ worker processes
- [ ] Worker handles 10 concurrent jobs (configured in `WorkerSettings`)
- [ ] Brand cache returns cached result within 24h

---

## Project Structure After Sprint 2

```
backend/
├── app/
│   ├── main.py                    # ✅ FastAPI app
│   ├── config.py                  # ✅ .env loading + PostgreSQL config
│   ├── database.py                # ✅ SQLite/PostgreSQL auto-detect
│   ├── api/v1/
│   │   ├── router.py              # ✅ Route aggregator
│   │   ├── brands.py              # ✅ Analyze endpoint + ARQ enqueue
│   │   ├── reports.py             # ✅ CRUD + SSE + tier-gated meta-ads
│   │   ├── subscriptions.py       # 🔄 Real Stripe checkout/portal
│   │   ├── credits.py             # ✅ Credit balance + history
│   │   └── webhooks.py            # 🔄 Real Stripe webhook handler
│   ├── core/
│   │   ├── clerk.py               # 🔄 Clerk SDK integration
│   │   ├── deps.py                # ✅ JWT verification + user resolution
│   │   ├── credit_guard.py        # ✅ Credit deduction
│   │   ├── rate_limit.py          # ✅ In-memory rate limiter
│   │   ├── subscription_guard.py  # ✅ Tier gate decorator
│   │   └── security.py            # ✅ Bearer scheme
│   ├── models/                    # ✅ All 8 models
│   ├── schemas/                   # ✅ Pydantic schemas
│   ├── jobs/
│   │   └── report_worker.py       # ✅ ARQ-compatible worker
│   ├── services/
│   │   ├── stripe.py              # 🔄 Real Stripe SDK
│   │   └── email.py               # 🔄 Real Resend SDK
│   └── prompts/
│       ├── loader.py              # ✅ YAML + Jinja2 loader
│       └── templates/             # ✅ 5 YAML templates
├── engine/
│   ├── orchestrator.py            # 🔄 Cost tracking added
│   ├── providers/                 # ✅ 7 providers
│   └── scorers/                   # 🔄 YAML prompts
├── migrations/                    # 🔄 Alembic migrations
├── alembic.ini                    # 🔄 Alembic config
├── arq_worker.py                  # ✅ ARQ entrypoint
├── pyproject.toml                 # ✅ Dependencies
└── .env                           # 🔄 Add Stripe + Clerk + PostgreSQL keys
```

✅ = Done in Sprint 1
🔄 = Sprint 2 work

---

## How to Build (Order)

1. **PostgreSQL + Alembic first** — foundation change, affects everything
2. **Cost Tracking** — touches orchestrator, easy win, no external deps
3. **Prompt YAML** — pure refactor, no new deps
4. **Stripe Integration** — needs real Stripe keys
5. **Clerk Auth** — needs real Clerk project setup
6. **ARQ Worker** — needs Redis, optional (thread fallback works)

---

## Estimated Effort

| Deliverable | Effort |
|-------------|--------|
| PostgreSQL + Alembic | 2-3 hours |
| Cost Tracking | 1 hour |
| Prompt YAML Extraction | 1 hour |
| Stripe Integration | 2-3 hours |
| Clerk Auth | 1-2 hours |
| ARQ Worker | 1-2 hours |
| **Total** | **~10 hours** |
